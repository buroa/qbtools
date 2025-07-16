package commands

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"

	"github.com/autobrr/go-qbittorrent"
	"github.com/rs/zerolog/log"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

// reannounceOptions holds all the flags for the reannounce command
type reannounceOptions struct {
	maxAge         int
	maxRetries     int
	interval       int
	processSeeding bool
}

// parseReannounceFlags extracts all command flags into a reannounceOptions struct
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

// NewReannounceCommand creates the reannounce command
func NewReannounceCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "reannounce",
		Short: "Reannounce torrents that have invalid trackers",
		Long:  `Reannounce torrents that have invalid trackers.`,
		RunE:  runReannounce,
	}

	cmd.Flags().Int("max-age", 3600, "The maximum age of a torrent in seconds to reannounce")
	cmd.Flags().Int("max-retries", qbittorrent.ReannounceMaxAttempts, "The maximum number of reannounce retries for a torrent")
	cmd.Flags().Int("interval", qbittorrent.ReannounceInterval, "The interval to process reannouncements in seconds")
	cmd.Flags().Bool("process-seeding", false, "Process seeding torrents as well")

	return cmd
}

func runReannounce(cmd *cobra.Command, args []string) error {
	client := qbittorrent.NewClient(qbittorrent.Config{
		Host:     viper.GetString("qbittorrent_host"),
		Username: viper.GetString("qbittorrent_username"),
		Password: viper.GetString("qbittorrent_password"),
	})

	// Login to the qBittorrent client
	if err := client.Login(); err != nil {
		return fmt.Errorf("failed to login to qBittorrent: %w", err)
	}

	ctx := cmd.Context()

	// Parse command flags
	opts, err := parseReannounceFlags(cmd)
	if err != nil {
		return fmt.Errorf("failed to parse flags: %w", err)
	}

	log.Info().Msg("Starting reannounce process...")

	// Main loop
	for {
		filter := qbittorrent.TorrentFilterStalledDownloading
		if opts.processSeeding {
			filter = qbittorrent.TorrentFilterStalled
		}

		// Get torrents with the specified filter
		torrents, err := client.GetTorrents(qbittorrent.TorrentFilterOptions{
			Filter:          filter,
			IncludeTrackers: true,
		})
		if err != nil {
			return fmt.Errorf("failed to get torrents: %w", err)
		}

		// Create a wait group to wait for all goroutines to complete
		var wg sync.WaitGroup

		// Process torrents in parallel
		for _, torrent := range torrents {
			if shouldReannounce(torrent, opts.maxAge) {
				wg.Add(1)
				go func(t qbittorrent.Torrent) {
					defer wg.Done()
					if err := reannounceWithRetry(ctx, client, t, opts.maxRetries, opts.interval); err != nil {
						log.Error().Err(err).Str("torrent_name", t.Name).Str("torrent_hash", t.Hash).Msg("Failed to reannounce torrent")
					} else {
						log.Info().Str("torrent_name", t.Name).Str("torrent_hash", t.Hash).Msg("Reannounced torrent")
					}
				}(torrent)
			}
		}

		// Wait for all goroutines to complete
		wg.Wait()

		time.Sleep(time.Duration(5) * time.Second)
	}
}

// shouldReannounce determines if a torrent needs to be reannounced based on tracker state
func shouldReannounce(torrent qbittorrent.Torrent, maxAge int) bool {
	// Skip if torrent is too old
	if torrent.TimeActive > int64(maxAge) {
		return false
	}

	// Skip if torrent has active peers
	if torrent.NumSeeds > 0 || torrent.NumLeechs > 0 {
		return false
	}

	// Check if any tracker is working (OK status)
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
		DeleteOnFailure: false, // Don't delete on failure by default
	}

	if err := client.ReannounceTorrentWithRetry(ctx, torrent.Hash, &opts); err != nil {
		if errors.Is(err, qbittorrent.ErrReannounceTookTooLong) {
			return fmt.Errorf("re-announce took too long for hash: %s", torrent.Hash)
		}
		return fmt.Errorf("could not reannounce torrent %s: %w", torrent.Hash, err)
	}

	return nil
}
