package logger

import (
	"os"
	"time"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

// Logger is the global logger instance
var Logger zerolog.Logger

// Initialize sets up the global logger
func Initialize(level string) {
	// Set up console writer for human-readable output
	consoleWriter := zerolog.ConsoleWriter{
		Out:        os.Stdout,
		TimeFormat: time.RFC3339,
		FormatMessage: func(i interface{}) string {
			return i.(string)
		},
	}

	// Create global logger
	Logger = zerolog.New(consoleWriter).With().Timestamp().Logger()

	// Set global logger
	log.Logger = Logger

	// Set log level based on parameter
	switch level {
	case "debug":
		zerolog.SetGlobalLevel(zerolog.DebugLevel)
	case "info":
		zerolog.SetGlobalLevel(zerolog.InfoLevel)
	case "warn":
		zerolog.SetGlobalLevel(zerolog.WarnLevel)
	case "error":
		zerolog.SetGlobalLevel(zerolog.ErrorLevel)
	default:
		zerolog.SetGlobalLevel(zerolog.InfoLevel)
	}
}

// SetLevel sets the log level
func SetLevel(level zerolog.Level) {
	zerolog.SetGlobalLevel(level)
}

// GetLogger returns the global logger instance
func GetLogger() zerolog.Logger {
	return Logger
}
