package commands

import (
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
		"UNREGISTERED",
		"TORRENT NOT FOUND",
		"TORRENT IS NOT",
		"NOT REGISTERED",
		"NOT EXIST",
		"UNKNOWN TORRENT",
		"TRUMP",
		"RETITLED",
		"INFOHASH NOT FOUND",
		"TORRENT HAS BEEN DELETED",
		"DEAD",
		"DUPE",
		"COMPLETE SEASON UPLOADED",
		"PROBLEM",
		"POSTPONED",
		"SPECIFICALLY BANNED",
		"OTHER",
		"NUKED",
		"INVALID INFOHASH",
	}

	maintenanceMatches = []string{
		"DOWN",
		"UNREACHABLE",
		"BAD GATEWAY",
		"TRACKER UNAVAILABLE",
	}
)

// taggingOptions holds all the flags for the tagging command
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

// parseFlags extracts all command flags into a taggingOptions struct
func parseFlags(cmd *cobra.Command) (*taggingOptions, error) {
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

// filterTorrents filters torrents based on exclude categories and tags
func filterTorrents(torrents []qbittorrent.Torrent, opts *taggingOptions) []qbittorrent.Torrent {
	filtered := torrents

	// Filter by categories
	if len(opts.excludeCategories) > 0 {
		var result []qbittorrent.Torrent
		for _, torrent := range filtered {
			excluded := false
			for _, exc := range opts.excludeCategories {
				if torrent.Category == exc {
					excluded = true
					break
				}
			}
			if !excluded {
				result = append(result, torrent)
			}
		}
		filtered = result
	}

	// Filter by tags
	if len(opts.excludeTags) > 0 {
		var result []qbittorrent.Torrent
		for _, torrent := range filtered {
			excluded := false
			for _, exc := range opts.excludeTags {
				if strings.Contains(torrent.Tags, exc) {
					excluded = true
					break
				}
			}
			if !excluded {
				result = append(result, torrent)
			}
		}
		filtered = result
	}

	return filtered
}

// getTrackerConfig returns the tracker configuration for a given torrent
func getTrackerConfig(torrent qbittorrent.Torrent, trackerMap map[string]config.TrackerConfig) *config.TrackerConfig {
	tracker := torrent.Tracker
	if tracker == "" {
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

// checkTrackerMessages checks if any tracker messages contain the given matches
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

// getTrackerStatusTags returns tracker status tags for a torrent
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
		Long: `Tag torrents. This command can be used to tag torrents with various tags,
such as torrents that have not been active for a while, torrents that have not been
working for a while, torrents that have expired an ratio or seeding time, torrents
that have the same content path, etc.`,
		RunE: runTagging,
	}

	cmd.Flags().StringSlice("exclude-category", []string{}, "Exclude all torrents with these categories")
	cmd.Flags().StringSlice("exclude-tag", []string{}, "Exclude all torrents with these tags")
	cmd.Flags().Bool("added-on", false, "Tag torrents with added date (last 24h, 7 days, 30 days, etc)")
	cmd.Flags().Bool("duplicates", false, "Tag torrents with the same content path")
	cmd.Flags().Bool("expired", false, "Tag torrents that have an expired ratio or seeding time")
	cmd.Flags().Bool("last-activity", false, "Tag torrents with last activity date")
	cmd.Flags().Bool("not-linked", false, "Tag torrents with files without hardlinks or symlinks")
	cmd.Flags().Bool("not-working", false, "Tag torrents with not working tracker status")
	cmd.Flags().Bool("sites", false, "Tag torrents with site names")
	cmd.Flags().Bool("tracker-down", false, "Tag torrents with temporarily down trackers")
	cmd.Flags().Bool("unregistered", false, "Tag torrents with unregistered tracker status message")

	return cmd
}

func runTagging(cmd *cobra.Command, args []string) error {
	log.Info().Msg("Tagging torrents in qBittorrent...")

	client := qbittorrent.NewClient(qbittorrent.Config{
		Host:     viper.GetString("qbittorrent_host"),
		Username: viper.GetString("qbittorrent_username"),
		Password: viper.GetString("qbittorrent_password"),
	})

	if err := client.Login(); err != nil {
		return fmt.Errorf("failed to login to qBittorrent: %w", err)
	}

	ctx := cmd.Context()

	opts, err := parseFlags(cmd)
	if err != nil {
		return fmt.Errorf("failed to parse flags: %w", err)
	}

	// Get all torrents
	torrents, err := client.GetTorrents(qbittorrent.TorrentFilterOptions{
		IncludeTrackers: true,
	})
	if err != nil {
		return fmt.Errorf("failed to get torrents: %w", err)
	}

	// Filter torrents based on exclude options
	torrents = filterTorrents(torrents, opts)

	// Get tracker configuration
	var trackers []config.TrackerConfig
	if err := viper.UnmarshalKey("trackers", &trackers); err != nil {
		return fmt.Errorf("failed to unmarshal trackers config: %w", err)
	}

	// Build tracker URL mapping
	trackerMap := make(map[string]config.TrackerConfig)
	for _, tracker := range trackers {
		for _, url := range tracker.URLs {
			trackerMap[url] = tracker
		}
	}

	now := time.Now()
	paths := make(map[string]bool)

	for _, torrent := range torrents {
		var tagsToAdd []string
		trackerConfig := getTrackerConfig(torrent, trackerMap)

		// Date-based tags
		if opts.addedOn && torrent.AddedOn > 0 {
			tag := utils.CalculateDateTags("added", torrent.AddedOn, now)
			tagsToAdd = append(tagsToAdd, tag)
		}

		if opts.lastActivity && torrent.LastActivity > 0 {
			tag := utils.CalculateDateTags("activity", torrent.LastActivity, now)
			tagsToAdd = append(tagsToAdd, tag)
		}

		// Site tags
		if opts.sites {
			siteTag := "site:unmapped"
			if trackerConfig != nil {
				siteTag = fmt.Sprintf("site:%s", trackerConfig.Name)
			} else {
				log.Warn().Str("tracker", torrent.Tracker).Msg("No tracker config found for site tag")
			}
			tagsToAdd = append(tagsToAdd, siteTag)
		}

		// Tracker status tags
		if opts.unregistered || opts.trackerDown || opts.notWorking {
			tagsToAdd = append(tagsToAdd, getTrackerStatusTags(torrent, opts)...)
		}

		// Expired torrents
		if opts.expired && trackerConfig != nil {
			if (trackerConfig.Ratio != 0 && torrent.Ratio >= trackerConfig.Ratio) ||
				(trackerConfig.Days != 0 && torrent.SeedingTime >= utils.SecondsFromDays(trackerConfig.Days)) {
				tagsToAdd = append(tagsToAdd, "expired")
			}
		}

		// Duplicate content paths
		if opts.duplicates && torrent.ContentPath != "" {
			if paths[torrent.ContentPath] && torrent.ContentPath != torrent.SavePath {
				tagsToAdd = append(tagsToAdd, "dupe")
			} else {
				paths[torrent.ContentPath] = true
			}
		}

		// Not linked files
		if opts.notLinked && torrent.ContentPath != "" && !utils.IsLinked(torrent.ContentPath) {
			tagsToAdd = append(tagsToAdd, "not-linked")
		}

		// Split on comma and trim spaces
		currentTags := strings.Split(torrent.Tags, ",")
		for i := range currentTags {
			currentTags[i] = strings.TrimSpace(currentTags[i])
		}

		// Check if tagsToAdd are already present
		if !utils.AreSetsEqual(currentTags, tagsToAdd) {
			newTags := strings.Join(tagsToAdd, ", ")
			client.SetTags(ctx, []string{torrent.Hash}, newTags)
			log.Info().Str("tags", newTags).Str("name", torrent.Name).Str("hash", torrent.Hash).Msg("Updated torrent tags")
		}
	}

	log.Info().Msg("Finished tagging torrents in qBittorrent")
	return nil
}
