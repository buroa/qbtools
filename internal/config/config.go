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

	// Set up viper to read the config file
	viper.SetConfigType("yaml")
	viper.SetConfigName("config")
	viper.AddConfigPath(".")
	viper.AddConfigPath(configPath)
	viper.AutomaticEnv()

	// read config
	if err := viper.ReadInConfig(); err != nil {
		log.Printf("config read error: %q", err)
	}

	// Unmarshal config into struct
	if err := viper.Unmarshal(c); err != nil {
		log.Fatalf("Could not unmarshal config file: %v: err %q", viper.ConfigFileUsed(), err)
	}

	return c
}
