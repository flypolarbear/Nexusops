package config

import (
	"fmt"
	"os"

	"github.com/spf13/viper"
)

type Config struct {
	Environment string `mapstructure:"environment"`
	Server      ServerConfig
	Database    DatabaseConfig
	Auth        AuthConfig
	Services    ServicesConfig
}

type ServerConfig struct {
	Port int    `mapstructure:"port"`
	Host string `mapstructure:"host"`
}

type DatabaseConfig struct {
	Host     string `mapstructure:"host"`
	Port     int    `mapstructure:"port"`
	User     string `mapstructure:"user"`
	Password string `mapstructure:"password"`
	Database string `mapstructure:"database"`
	SSLMode  string `mapstructure:"ssl_mode"`
}

func (d *DatabaseConfig) DSN() string {
	return fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
		d.Host, d.Port, d.User, d.Password, d.Database, d.SSLMode,
	)
}

type AuthConfig struct {
	OIDCIssuer    string `mapstructure:"oidc_issuer"`
	LDAPServer    string `mapstructure:"ldap_server"`
	JWTSecret     string `mapstructure:"jwt_secret"`
	TokenDuration int    `mapstructure:"token_duration"`
}

type ServicesConfig struct {
	GrafanaURL   string `mapstructure:"grafana_url"`
	ArgoCDURL    string `mapstructure:"argocd_url"`
	JenkinsURL   string `mapstructure:"jenkins_url"`
	HarborURL    string `mapstructure:"harbor_url"`
	OpenclawURL  string `mapstructure:"openclaw_url"`
	Kubeconfig   string `mapstructure:"kubeconfig"`
}

func Load() (*Config, error) {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath("./config")
	viper.AddConfigPath("./cmd/api-gateway/config")
	viper.AddConfigPath("/etc/nexusops")

	// Environment variable overrides
	viper.AutomaticEnv()
	viper.SetEnvPrefix("NEXUSOPS")

	// Defaults
	viper.SetDefault("environment", "development")
	viper.SetDefault("server.port", 8080)
	viper.SetDefault("server.host", "0.0.0.0")
	viper.SetDefault("database.port", 5432)
	viper.SetDefault("database.ssl_mode", "disable")
	viper.SetDefault("auth.token_duration", 3600)

	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			return nil, fmt.Errorf("error reading config: %w", err)
		}
		// Config file not found, use env vars and defaults
	}

	var cfg Config
	if err := viper.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("error unmarshaling config: %w", err)
	}

	// Override with env vars if set
	if env := os.Getenv("NEXUSOPS_ENV"); env != "" {
		cfg.Environment = env
	}
	if dbHost := os.Getenv("DB_HOST"); dbHost != "" {
		cfg.Database.Host = dbHost
	}
	if dbPass := os.Getenv("DB_PASSWORD"); dbPass != "" {
		cfg.Database.Password = dbPass
	}

	return &cfg, nil
}
