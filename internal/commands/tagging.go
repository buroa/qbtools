package commands

import (
	"context"
	"fmt"
	"net/url"
	"strings"
	"time"

	"github.com/autobrr/go-qbittorrent"
	"github.com/buroa/qbtools/internal/config"
	"github.com/buroa/qbtools/internal/utils"
	"github.com/rs/zerolog/log"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"golang.org/x/net/publicsuffix"
)

const (
	TrackerStatusUnregistered = "unregistered"
	TrackerStatusDown         = "down"
	TrackerStatusNotWorking   = "not-working"
)

var (
	unregisteredMatches = []string{
		"UNREGISTERED", "TORRENT NOT FOUND", "TORRENT IS NOT", "NOT REGISTERED",
		"NOT EXIST", "UNKNOWN TORRENT", "TRUMP", "RETITLED", "INFOHASH NOT FOUND",
		"TORRENT HAS BEEN DELETED", "DEAD", "DUPE", "COMPLETE SEASON UPLOADED",
		"PROBLEM", "POSTPONED", "SPECIFICALLY BANNED", "OTHER", "NUKED", "INVALID INFOHASH",
	}

	maintenanceMatches = []string{
		"DOWN", "UNREACHABLE", "BAD GATEWAY", "TRACKER UNAVAILABLE",
	}
)

type taggingOptions struct {
	excludeCategories []string
	excludeTags       []string
	addedOn           bool
	duplicates        bool
	expired           bool
	lastActivity      bool
	notLinked         bool
	notWorking        bool
	sites             bool
	trackerDown       bool
	unregistered      bool
}

func parseTaggingFlags(cmd *cobra.Command) (*taggingOptions, error) {
	opts := &taggingOptions{}
	var err error

	if opts.excludeCategories, err = cmd.Flags().GetStringSlice("exclude-category"); err != nil {
		return nil, err
	}
	if opts.excludeTags, err = cmd.Flags().GetStringSlice("exclude-tag"); err != nil {
		return nil, err
	}
	if opts.addedOn, err = cmd.Flags().GetBool("added-on"); err != nil {
		return nil, err
	}
	if opts.duplicates, err = cmd.Flags().GetBool("duplicates"); err != nil {
		return nil, err
	}
	if opts.expired, err = cmd.Flags().GetBool("expired"); err != nil {
		return nil, err
	}
	if opts.lastActivity, err = cmd.Flags().GetBool("last-activity"); err != nil {
		return nil, err
	}
	if opts.notLinked, err = cmd.Flags().GetBool("not-linked"); err != nil {
		return nil, err
	}
	if opts.notWorking, err = cmd.Flags().GetBool("not-working"); err != nil {
		return nil, err
	}
	if opts.sites, err = cmd.Flags().GetBool("sites"); err != nil {
		return nil, err
	}
	if opts.trackerDown, err = cmd.Flags().GetBool("tracker-down"); err != nil {
		return nil, err
	}
	if opts.unregistered, err = cmd.Flags().GetBool("unregistered"); err != nil {
		return nil, err
	}

	return opts, nil
}

func filterTorrents(torrents []qbittorrent.Torrent, opts *taggingOptions) []qbittorrent.Torrent {
	filtered := torrents

	filtered = filterByExclusions(filtered, opts.excludeCategories, func(torrent qbittorrent.Torrent, exclude string) bool {
		return torrent.Category == exclude
	})

	filtered = filterByExclusions(filtered, opts.excludeTags, func(torrent qbittorrent.Torrent, exclude string) bool {
		return strings.Contains(torrent.Tags, exclude)
	})

	return filtered
}

func filterByExclusions(torrents []qbittorrent.Torrent, exclusions []string, matchFunc func(qbittorrent.Torrent, string) bool) []qbittorrent.Torrent {
	if len(exclusions) == 0 {
		return torrents
	}

	var result []qbittorrent.Torrent
	for _, torrent := range torrents {
		excluded := false
		for _, exc := range exclusions {
			if matchFunc(torrent, exc) {
				excluded = true
				break
			}
		}
		if !excluded {
			result = append(result, torrent)
		}
	}
	return result
}

// getTrackerConfig returns the tracker configuration for a torrent's primary tracker
func getTrackerConfig(torrent qbittorrent.Torrent, trackerMap map[string]config.TrackerConfig) *config.TrackerConfig {
	tracker := torrent.Tracker
	if tracker == "" && len(torrent.Trackers) > 0 {
		tracker = torrent.Trackers[0].Url
	}

	parsedURL, err := url.Parse(tracker)
	if err != nil {
		return nil
	}

	tldPlusOne, err := publicsuffix.EffectiveTLDPlusOne(parsedURL.Hostname())
	if err != nil {
		return nil
	}

	domain := strings.ToLower(tldPlusOne)
	if tc, exists := trackerMap[domain]; exists {
		return &tc
	}

	return nil
}

func checkTrackerMessages(messages []string, matches []string) bool {
	for _, match := range matches {
		for _, msg := range messages {
			if strings.Contains(msg, match) {
				return true
			}
		}
	}
	return false
}

// getTrackerStatusTags determines appropriate status tags based on tracker messages
func getTrackerStatusTags(torrent qbittorrent.Torrent, opts *taggingOptions) []string {
	var messages []string

	for _, tracker := range torrent.Trackers {
		if tracker.Status == qbittorrent.TrackerStatusOK {
			return nil
		}
		messages = append(messages, strings.ToUpper(tracker.Message))
	}

	if opts.unregistered && checkTrackerMessages(messages, unregisteredMatches) {
		return []string{TrackerStatusUnregistered}
	}

	if opts.trackerDown && checkTrackerMessages(messages, maintenanceMatches) {
		return []string{TrackerStatusDown}
	}

	return []string{TrackerStatusNotWorking}
}

// NewTaggingCommand creates the tagging command
func NewTaggingCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "tagging",
		Short: "Tag torrents with various criteria",
		Long: `Tag torrents based on various criteria including activity dates, tracker status,
duplicate content paths, expired ratios, and site information.`,
		RunE: runTagging,
	}

	cmd.Flags().StringSlice("exclude-category", []string{}, "Exclude torrents with these categories")
	cmd.Flags().StringSlice("exclude-tag", []string{}, "Exclude torrents with these tags")
	cmd.Flags().Bool("added-on", false, "Tag torrents by added date (24h, 7d, 30d, 180d, >180d)")
	cmd.Flags().Bool("duplicates", false, "Tag torrents with duplicate content paths")
	cmd.Flags().Bool("expired", false, "Tag torrents that have expired ratio or seeding time")
	cmd.Flags().Bool("last-activity", false, "Tag torrents by last activity date")
	cmd.Flags().Bool("not-linked", false, "Tag torrents with files missing hardlinks or symlinks")
	cmd.Flags().Bool("not-working", false, "Tag torrents with non-working tracker status")
	cmd.Flags().Bool("sites", false, "Tag torrents with site names")
	cmd.Flags().Bool("tracker-down", false, "Tag torrents with temporarily unavailable trackers")
	cmd.Flags().Bool("unregistered", false, "Tag torrents with unregistered tracker status")

	return cmd
}

func runTagging(cmd *cobra.Command, args []string) error {
	log.Info().Msg("Starting torrent tagging process")

	client := qbittorrent.NewClient(qbittorrent.Config{
		Host:     viper.GetString("qbittorrent_host"),
		Username: viper.GetString("qbittorrent_username"),
		Password: viper.GetString("qbittorrent_password"),
	})

	if err := client.Login(); err != nil {
		return fmt.Errorf("failed to authenticate with qBittorrent: %w", err)
	}

	opts, err := parseTaggingFlags(cmd)
	if err != nil {
		return fmt.Errorf("failed to parse command flags: %w", err)
	}

	torrents, err := client.GetTorrents(qbittorrent.TorrentFilterOptions{
		IncludeTrackers: true,
	})
	if err != nil {
		return fmt.Errorf("failed to retrieve torrents: %w", err)
	}

	log.Debug().Int("count", len(torrents)).Msg("Retrieved torrents from qBittorrent")

	torrents = filterTorrents(torrents, opts)

	log.Debug().Int("count", len(torrents)).Msg("Filtered torrents for processing")

	trackerMap, err := buildTrackerMap()
	if err != nil {
		return fmt.Errorf("failed to build tracker configuration map: %w", err)
	}

	return processTorrents(client, cmd.Context(), torrents, trackerMap, opts)
}

func buildTrackerMap() (map[string]config.TrackerConfig, error) {
	var trackers []config.TrackerConfig
	if err := viper.UnmarshalKey("trackers", &trackers); err != nil {
		return nil, fmt.Errorf("failed to unmarshal tracker configuration: %w", err)
	}

	trackerMap := make(map[string]config.TrackerConfig)
	for _, tracker := range trackers {
		for _, url := range tracker.URLs {
			trackerMap[url] = tracker
		}
	}

	return trackerMap, nil
}

func processTorrents(client *qbittorrent.Client, ctx context.Context, torrents []qbittorrent.Torrent, trackerMap map[string]config.TrackerConfig, opts *taggingOptions) error {
	now := time.Now()
	paths := make(map[string]bool)

	for _, torrent := range torrents {
		var tagsToAdd []string
		trackerConfig := getTrackerConfig(torrent, trackerMap)

		// Apply date-based tags
		if opts.addedOn && torrent.AddedOn > 0 {
			tagsToAdd = append(tagsToAdd, utils.CalculateDateTags("added", torrent.AddedOn, now))
		}

		if opts.lastActivity && torrent.LastActivity > 0 {
			tagsToAdd = append(tagsToAdd, utils.CalculateDateTags("activity", torrent.LastActivity, now))
		}

		// Apply site tags
		if opts.sites {
			siteTag := "site:unmapped"
			if trackerConfig != nil {
				siteTag = fmt.Sprintf("site:%s", trackerConfig.Name)
			} else if torrent.Tracker != "" {
				log.Warn().Str("tracker", torrent.Tracker).Str("hash", torrent.Hash).Msg("No tracker configuration found for torrent")
			}
			tagsToAdd = append(tagsToAdd, siteTag)
		}

		// Apply tracker status tags
		if opts.unregistered || opts.trackerDown || opts.notWorking {
			if statusTags := getTrackerStatusTags(torrent, opts); len(statusTags) > 0 {
				tagsToAdd = append(tagsToAdd, statusTags...)
			}
		}

		// Apply expiration tags
		if opts.expired && trackerConfig != nil {
			if (trackerConfig.Ratio != 0 && torrent.Ratio >= trackerConfig.Ratio) ||
				(trackerConfig.Days != 0 && torrent.SeedingTime >= utils.SecondsFromDays(trackerConfig.Days)) {
				tagsToAdd = append(tagsToAdd, "expired")
			}
		}

		// Apply duplicate content path tags
		if opts.duplicates && torrent.ContentPath != "" {
			if paths[torrent.ContentPath] && torrent.ContentPath != torrent.SavePath {
				tagsToAdd = append(tagsToAdd, "dupe")
			} else {
				paths[torrent.ContentPath] = true
			}
		}

		// Apply not-linked tags
		if opts.notLinked && torrent.ContentPath != "" && !utils.IsLinked(torrent.ContentPath) {
			tagsToAdd = append(tagsToAdd, "not-linked")
		}

		// Update tags if they have changed
		if len(tagsToAdd) > 0 {
			currentTags := strings.Split(torrent.Tags, ",")
			for i := range currentTags {
				currentTags[i] = strings.TrimSpace(currentTags[i])
			}

			if !utils.AreSetsEqual(currentTags, tagsToAdd) {
				newTags := strings.Join(tagsToAdd, ", ")
				if err := client.SetTags(ctx, []string{torrent.Hash}, newTags); err != nil {
					log.Error().Err(err).Str("hash", torrent.Hash).Msg("Failed to update torrent tags")
					continue
				}
				log.Info().Str("tags", newTags).Str("hash", torrent.Hash).Msg("Updated torrent tags")
			}
		}
	}

	log.Info().Msg("Torrent tagging process completed")
	return nil
}
