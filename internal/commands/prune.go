package commands

import (
	"fmt"
	"path/filepath"
	"slices"
	"strings"

	"github.com/autobrr/go-qbittorrent"
	"github.com/rs/zerolog/log"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

type pruneOptions struct {
	includeTags       []string
	excludeTags       []string
	includeCategories []string
	excludeCategories []string
	dryRun            bool
	withData          bool
}

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

func filterTorrentsByTags(torrents []qbittorrent.Torrent, tags []string, requireAll bool) []qbittorrent.Torrent {
	if len(tags) == 0 {
		return torrents
	}

	var filtered []qbittorrent.Torrent
	for _, torrent := range torrents {
		if requireAll {
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

func NewPruneCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "prune",
		Short: "Prune torrents that have matching tags",
		Long:  `Prune torrents based on tag criteria. Use in combination with the tagging command.`,
		RunE:  runPrune,
	}

	cmd.Flags().StringSlice("include-tag", []string{}, "Include torrents containing all of these tags")
	cmd.Flags().StringSlice("exclude-tag", []string{}, "Exclude torrents containing any of these tags")
	cmd.Flags().StringSlice("include-category", []string{}, "Include torrents only from categories matching these patterns")
	cmd.Flags().StringSlice("exclude-category", []string{}, "Exclude torrents from categories matching these patterns")
	cmd.Flags().Bool("dry-run", false, "Preview deletion without actually removing torrents")
	cmd.Flags().Bool("with-data", false, "Delete torrents along with their data files")

	cmd.MarkFlagRequired("include-tag")

	return cmd
}

func runPrune(cmd *cobra.Command, args []string) error {
	log.Debug().Msg("Starting torrent pruning process")

	client := qbittorrent.NewClient(qbittorrent.Config{
		Host:     viper.GetString("qbittorrent_host"),
		Username: viper.GetString("qbittorrent_username"),
		Password: viper.GetString("qbittorrent_password"),
	})

	if err := client.Login(); err != nil {
		return fmt.Errorf("failed to authenticate with qBittorrent: %w", err)
	}

	opts, err := parsePruneFlags(cmd)
	if err != nil {
		return fmt.Errorf("failed to parse command flags: %w", err)
	}

	categoriesResp, err := client.GetCategories()
	if err != nil {
		return fmt.Errorf("failed to retrieve categories: %w", err)
	}

	categories := make([]string, 0, len(categoriesResp))
	for name := range categoriesResp {
		categories = append(categories, name)
	}

	categories = filterCategoriesByPatterns(categories, opts.includeCategories, true)
	categories = filterCategoriesByPatterns(categories, opts.excludeCategories, false)

	if len(categories) == 0 {
		log.Info().Msg("No torrents to prune - no categories match the specified criteria")
		return nil
	}

	torrents, err := client.GetTorrents(qbittorrent.TorrentFilterOptions{})
	if err != nil {
		return fmt.Errorf("failed to retrieve torrents: %w", err)
	}

	var filteredTorrents []qbittorrent.Torrent
	for _, torrent := range torrents {
		if slices.Contains(categories, torrent.Category) {
			filteredTorrents = append(filteredTorrents, torrent)
		}
	}

	filteredTorrents = filterTorrentsByTags(filteredTorrents, opts.includeTags, true)
	filteredTorrents = filterTorrentsByTags(filteredTorrents, opts.excludeTags, false)

	if len(filteredTorrents) == 0 {
		log.Info().Msg("No torrents match the pruning criteria")
		return nil
	}

	log.Info().
		Str("include_tags", strings.Join(opts.includeTags, " AND ")).
		Str("exclude_tags", strings.Join(opts.excludeTags, " OR ")).
		Int("count", len(filteredTorrents)).
		Msg("Torrents selected for pruning")

	var torrentHashes []string
	for _, torrent := range filteredTorrents {
		torrentHashes = append(torrentHashes, torrent.Hash)
		log.Info().Str("hash", torrent.Hash).Str("tags", torrent.Tags).Msg("Torrent selected for deletion")
	}

	if opts.dryRun {
		return nil
	}

	if err := client.DeleteTorrents(torrentHashes, opts.withData); err != nil {
		return fmt.Errorf("failed to delete torrents: %w", err)
	}

	log.Info().
		Int("deleted", len(filteredTorrents)).
		Bool("with_data", opts.withData).
		Msg("Torrent pruning completed successfully")

	return nil
}
