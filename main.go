package main

import (
	"github.com/buroa/qbtools/internal/commands"
	"github.com/buroa/qbtools/internal/config"
	"github.com/buroa/qbtools/internal/logger"
	"github.com/rs/zerolog/log"
	"github.com/spf13/cobra"
)

func main() {
	rootCmd := &cobra.Command{
		Use:   "qbtools",
		Short: "Feature-rich CLI for qBittorrent management",
		Long:  `qbtools is a feature-rich CLI for the management of torrents in qBittorrent.`,
		PersistentPreRun: func(cmd *cobra.Command, args []string) {
			logLevel, _ := cmd.Flags().GetString("log-level")
			logger.Initialize(logLevel)
			configFile, _ := cmd.Flags().GetString("config")
			config.Initialize(configFile)
		},
	}

	rootCmd.PersistentFlags().StringP("config", "c", "/config/config.yaml", "Path to configuration file")
	rootCmd.PersistentFlags().StringP("log-level", "l", "info", "Log level (debug, info, warn, error)")

	rootCmd.AddCommand(commands.NewTaggingCommand())
	rootCmd.AddCommand(commands.NewReannounceCommand())
	rootCmd.AddCommand(commands.NewPruneCommand())

	if err := rootCmd.Execute(); err != nil {
		log.Fatal().Err(err).Msg("Failed to execute command")
	}
}
