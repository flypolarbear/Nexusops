package main

import (
	"log"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/hendrix/nexusops/internal/config"
	"github.com/hendrix/nexusops/internal/middleware"
)

func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Setup Gin router
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()
	router.Use(gin.Recovery())
	router.Use(middleware.Logger())
	router.Use(middleware.CORS())

	// Health check
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "healthy", "service": "api-gateway"})
	})

	// API routes will be added here
	api := router.Group("/api/v1")
	{
		// Overview routes
		api.GET("/overview", getOverview)

		// Resource routes
		api.GET("/resources", getResources)

		// Deployment routes
		api.GET("/deployments", getDeployments)

		// Alert routes
		api.GET("/alerts", getAlerts)

		// Ticket routes
		api.GET("/tickets", getTickets)
		api.POST("/tickets", createTicket)

		// AI Assistant routes
		api.GET("/ai/query", aiQuery)
	}

	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("API Gateway starting on port %s", port)
	if err := router.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

// Handlers - will be moved to proper packages
func getOverview(c *gin.Context) {
	c.JSON(200, gin.H{
		"services": gin.H{"total": 0, "healthy": 0, "warning": 0, "critical": 0},
		"clusters": gin.H{"total": 0, "healthy": 0},
		"alerts":   gin.H{"total": 0, "critical": 0, "warning": 0},
	})
}

func getResources(c *gin.Context) {
	c.JSON(200, gin.H{"resources": []interface{}{}})
}

func getDeployments(c *gin.Context) {
	c.JSON(200, gin.H{"deployments": []interface{}{}})
}

func getAlerts(c *gin.Context) {
	c.JSON(200, gin.H{"alerts": []interface{}{}})
}

func getTickets(c *gin.Context) {
	c.JSON(200, gin.H{"tickets": []interface{}{}})
}

func createTicket(c *gin.Context) {
	c.JSON(201, gin.H{"id": "new-ticket-id"})
}

func aiQuery(c *gin.Context) {
	c.JSON(200, gin.H{
		"response": "AI query placeholder",
		"links":    []interface{}{},
	})
}
