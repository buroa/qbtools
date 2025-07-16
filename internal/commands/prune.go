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

// pruneOptions holds all the flags for the prune command
type pruneOptions struct {
	includeTags       []string
	excludeTags       []string
	includeCategories []string
	excludeCategories []string
	dryRun            bool
	withData          bool
}

// parsePruneFlags extracts all command flags into a pruneOptions struct
func parsePruneFlags(cmd *cobra.Command) (*pruneOptions, error) {
	opts := &pruneOptions{}
	var err error

	if opts.includeTags, err = cmd.Flags().GetStringSlice("include-tag"); err != nil {
		return nil, err
	}
	if opts.excludeTags, err = cmd.Flags().GetStringSlice("exclude-tag"); err != nil {
		return nil, err
	}
	if opts.includeCategories, err = cmd.Flags().GetStringSlice("include-category"); err != nil {
		return nil, err
	}
	if opts.excludeCategories, err = cmd.Flags().GetStringSlice("exclude-category"); err != nil {
		return nil, err
	}
	if opts.dryRun, err = cmd.Flags().GetBool("dry-run"); err != nil {
		return nil, err
	}
	if opts.withData, err = cmd.Flags().GetBool("with-data"); err != nil {
		return nil, err
	}

	return opts, nil
}

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

	// Parse command flags
	opts, err := parsePruneFlags(cmd)
	if err != nil {
		return fmt.Errorf("failed to parse flags: %w", err)
	}

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
	categories = filterCategoriesByPatterns(categories, opts.includeCategories, true)
	categories = filterCategoriesByPatterns(categories, opts.excludeCategories, false)

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
	filteredTorrents = filterTorrentsByTags(filteredTorrents, opts.includeTags, true)
	filteredTorrents = filterTorrentsByTags(filteredTorrents, opts.excludeTags, false)

	log.Info().
		Str("include_tags", strings.Join(opts.includeTags, " AND ")).
		Str("exclude_tags", strings.Join(opts.excludeTags, " OR ")).
		Msg("Pruning torrents with tags")

	// Log torrents to be deleted and collect their hashes
	var torrentHashes []string
	for _, torrent := range filteredTorrents {
		torrentHashes = append(torrentHashes, torrent.Hash)
	}

	// Delete all torrents in a single batch
	if !opts.dryRun && len(torrentHashes) > 0 {
		err := client.DeleteTorrents(torrentHashes, opts.withData)
		if err != nil {
			log.Error().Err(err).Msg("Failed to delete torrents")
		}
		log.Info().Msg("Torrents pruned successfully")
	}

	log.Info().Int("deleted_count", len(filteredTorrents)).Msg("Deleted torrents")
	return nil
}
