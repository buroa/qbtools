package commands

import (
	"fmt"
	"path/filepath"
	"strings"

	"github.com/autobrr/go-qbittorrent"
	"github.com/rs/zerolog/log"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

// filterTorrentsByTags filters torrents based on tag requirements
// If requireAll is true, torrent must have ALL tags (AND logic)
// If requireAll is false, torrent must NOT have ANY tags (exclude logic)
func filterTorrentsByTags(torrents []qbittorrent.Torrent, tags []string, requireAll bool) []qbittorrent.Torrent {
	if len(tags) == 0 {
		return torrents
	}

	var filtered []qbittorrent.Torrent
	for _, torrent := range torrents {
		if requireAll {
			// Include logic: torrent must have ALL tags
			hasAllTags := true
			for _, tag := range tags {
				if !strings.Contains(torrent.Tags, tag) {
					hasAllTags = false
					break
				}
			}
			if hasAllTags {
				filtered = append(filtered, torrent)
			}
		} else {
			// Exclude logic: torrent must NOT have ANY tags
			hasExcludeTag := false
			for _, tag := range tags {
				if strings.Contains(torrent.Tags, tag) {
					hasExcludeTag = true
					break
				}
			}
			if !hasExcludeTag {
				filtered = append(filtered, torrent)
			}
		}
	}
	return filtered
}

// filterCategoriesByPatterns filters categories based on patterns
// If include is true, only categories matching patterns are kept
// If include is false, categories matching patterns are excluded
func filterCategoriesByPatterns(categories []string, patterns []string, include bool) []string {
	if len(patterns) == 0 {
		return categories
	}

	var filtered []string
	for _, category := range categories {
		matched := false
		for _, pattern := range patterns {
			if match, _ := filepath.Match(pattern, category); match {
				matched = true
				break
			}
		}

		if include == matched {
			filtered = append(filtered, category)
		}
	}
	return filtered
}

// NewPruneCommand creates the prune command
func NewPruneCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "prune",
		Short: "Prune torrents that have matching tags",
		Long: `Prune torrents that have matching tags.
Pair this with the tagging command to tag torrents.`,
		RunE: runPrune,
	}

	cmd.Flags().StringSlice("include-tag", []string{}, "Include torrents containing all of these tags")
	cmd.Flags().StringSlice("exclude-tag", []string{}, "Exclude torrents containing any of these tags")
	cmd.Flags().StringSlice("include-category", []string{}, "Include torrents only from categories that match these patterns")
	cmd.Flags().StringSlice("exclude-category", []string{}, "Exclude torrents from categories that match these patterns")
	cmd.Flags().Bool("dry-run", false, "Do not delete torrents")
	cmd.Flags().Bool("with-data", false, "Delete torrents with data")

	cmd.MarkFlagRequired("include-tag")

	return cmd
}

func runPrune(cmd *cobra.Command, args []string) error {
	client := qbittorrent.NewClient(qbittorrent.Config{
		Host:     viper.GetString("qbittorrent_host"),
		Username: viper.GetString("qbittorrent_username"),
		Password: viper.GetString("qbittorrent_password"),
	})

	// Login to the qBittorrent client
	if err := client.Login(); err != nil {
		return fmt.Errorf("failed to login to qBittorrent: %w", err)
	}

	// Get command flags
	includeTags, _ := cmd.Flags().GetStringSlice("include-tag")
	excludeTags, _ := cmd.Flags().GetStringSlice("exclude-tag")
	includeCategories, _ := cmd.Flags().GetStringSlice("include-category")
	excludeCategories, _ := cmd.Flags().GetStringSlice("exclude-category")
	dryRun, _ := cmd.Flags().GetBool("dry-run")
	withData, _ := cmd.Flags().GetBool("with-data")

	// Get categories
	categoriesResp, err := client.GetCategories()
	if err != nil {
		return fmt.Errorf("failed to get categories: %w", err)
	}

	// Pre-allocate slice
	categories := make([]string, 0, len(categoriesResp))
	for name := range categoriesResp {
		categories = append(categories, name)
	}

	// Filter categories by include/exclude patterns
	categories = filterCategoriesByPatterns(categories, includeCategories, true)
	categories = filterCategoriesByPatterns(categories, excludeCategories, false)

	if len(categories) == 0 {
		log.Info().Msg("No torrents can be pruned since no categories were included based on selectors")
		return nil
	}

	// Get all torrents
	torrents, err := client.GetTorrents(qbittorrent.TorrentFilterOptions{})
	if err != nil {
		return fmt.Errorf("failed to get torrents: %w", err)
	}

	// Filter torrents by categories
	var filteredTorrents []qbittorrent.Torrent
	for _, torrent := range torrents {
		inCategory := false
		for _, cat := range categories {
			if torrent.Category == cat {
				inCategory = true
				break
			}
		}
		if inCategory {
			filteredTorrents = append(filteredTorrents, torrent)
		}
	}

	// Filter by include and exclude tags
	filteredTorrents = filterTorrentsByTags(filteredTorrents, includeTags, true)
	filteredTorrents = filterTorrentsByTags(filteredTorrents, excludeTags, false)

	log.Info().
		Str("include_tags", strings.Join(includeTags, " AND ")).
		Str("exclude_tags", strings.Join(excludeTags, " OR ")).
		Msg("Pruning torrents with tags")

	// Log torrents to be deleted and collect their hashes
	var torrentHashes []string
	for _, torrent := range filteredTorrents {
		torrentHashes = append(torrentHashes, torrent.Hash)
	}

	// Delete all torrents in a single batch
	if !dryRun && len(torrentHashes) > 0 {
		err := client.DeleteTorrents(torrentHashes, withData)
		if err != nil {
			log.Error().Err(err).Msg("Failed to delete torrents")
		}
		log.Info().Msg("Torrents pruned successfully")
	}

	log.Info().Int("deleted_count", len(filteredTorrents)).Msg("Deleted torrents")
	return nil
}
