package commands

import (
	"context"
	"errors"
	"fmt"
	"os"
	"sync"
	"time"

	"github.com/autobrr/go-qbittorrent"
	"github.com/rs/zerolog/log"
	"github.com/spf13/cobra"
)

type reannounceOptions struct {
	maxAge         int
	maxRetries     int
	interval       int
	processSeeding bool
}

func parseReannounceFlags(cmd *cobra.Command) (*reannounceOptions, error) {
	opts := &reannounceOptions{}
	var err error

	if opts.maxAge, err = cmd.Flags().GetInt("max-age"); err != nil {
		return nil, err
	}
	if opts.maxRetries, err = cmd.Flags().GetInt("max-retries"); err != nil {
		return nil, err
	}
	if opts.interval, err = cmd.Flags().GetInt("interval"); err != nil {
		return nil, err
	}
	if opts.processSeeding, err = cmd.Flags().GetBool("process-seeding"); err != nil {
		return nil, err
	}

	return opts, nil
}

func NewReannounceCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "reannounce",
		Short: "Reannounce torrents that have invalid trackers",
		Long:  `Reannounce torrents with invalid tracker status to refresh their connection.`,
		RunE:  runReannounce,
	}

	cmd.Flags().Int("max-age", 3600, "Maximum age of a torrent in seconds to reannounce")
	cmd.Flags().Int("max-retries", qbittorrent.ReannounceMaxAttempts, "Maximum number of reannounce retries per torrent")
	cmd.Flags().Int("interval", qbittorrent.ReannounceInterval, "Interval between reannouncement attempts in seconds")
	cmd.Flags().Bool("process-seeding", false, "Include seeding torrents in the reannouncement process")

	return cmd
}

func runReannounce(cmd *cobra.Command, args []string) error {
	log.Info().Msg("Starting torrent reannouncement process")

	client := qbittorrent.NewClient(qbittorrent.Config{
		Host:     os.Getenv("QBITTORRENT_HOST"),
		Username: os.Getenv("QBITTORRENT_USERNAME"),
		Password: os.Getenv("QBITTORRENT_PASSWORD"),
	})

	if err := client.Login(); err != nil {
		return fmt.Errorf("failed to authenticate with qBittorrent: %w", err)
	}

	opts, err := parseReannounceFlags(cmd)
	if err != nil {
		return fmt.Errorf("failed to parse command flags: %w", err)
	}

	ctx := cmd.Context()

	for {
		filter := qbittorrent.TorrentFilterStalledDownloading
		if opts.processSeeding {
			filter = qbittorrent.TorrentFilterStalled
		}

		torrents, err := client.GetTorrents(qbittorrent.TorrentFilterOptions{
			Filter:          filter,
			IncludeTrackers: true,
		})
		if err != nil {
			return fmt.Errorf("failed to retrieve torrents: %w", err)
		}

		var wg sync.WaitGroup

		for _, torrent := range torrents {
			if shouldReannounce(torrent, opts.maxAge) {
				wg.Add(1)
				go func(t qbittorrent.Torrent) {
					defer wg.Done()
					if err := reannounceWithRetry(ctx, client, t, opts.maxRetries, opts.interval); err != nil {
						log.Error().Err(err).Str("hash", t.Hash).Msg("Failed to reannounce torrent")
					} else {
						log.Info().Str("hash", t.Hash).Msg("Reannounced torrent")
					}
				}(torrent)
			}
		}

		wg.Wait()

		time.Sleep(5 * time.Second)
	}
}

func shouldReannounce(torrent qbittorrent.Torrent, maxAge int) bool {
	if torrent.TimeActive > int64(maxAge) {
		return false
	}

	if torrent.NumSeeds > 0 || torrent.NumLeechs > 0 {
		return false
	}

	for _, tracker := range torrent.Trackers {
		if tracker.Status == qbittorrent.TrackerStatusOK {
			return false
		}
	}

	return true
}

// reannounceWithRetry performs the reannounce operation with retry logic
func reannounceWithRetry(ctx context.Context, client *qbittorrent.Client, torrent qbittorrent.Torrent, maxAttempts, interval int) error {
	opts := qbittorrent.ReannounceOptions{
		Interval:        interval,
		MaxAttempts:     maxAttempts,
		DeleteOnFailure: false,
	}

	if err := client.ReannounceTorrentWithRetry(ctx, torrent.Hash, &opts); err != nil {
		if errors.Is(err, qbittorrent.ErrReannounceTookTooLong) {
			return fmt.Errorf("reannouncement timeout for torrent %s", torrent.Hash)
		}
		return fmt.Errorf("reannouncement failed for torrent %s: %w", torrent.Hash, err)
	}

	return nil
}
