package config

import (
	"log"

	"github.com/spf13/viper"
)

type Config struct {
	Trackers []TrackerConfig `yaml:"trackers"`
}

type TrackerConfig struct {
	Name  string   `yaml:"name"`
	URLs  []string `yaml:"urls"`
	Ratio float64  `yaml:"ratio"`
	Days  float64  `yaml:"days"`
}

func Initialize(configPath string) *Config {
	c := &Config{}

	viper.SetConfigType("yaml")
	viper.SetConfigName("config")
	viper.AddConfigPath(".")
	viper.AddConfigPath(configPath)
	viper.AutomaticEnv()

	if err := viper.ReadInConfig(); err != nil {
		log.Printf("Configuration read error: %q", err)
	}

	if err := viper.Unmarshal(c); err != nil {
		log.Fatalf("Failed to unmarshal configuration file %v: %q", viper.ConfigFileUsed(), err)
	}

	return c
}
