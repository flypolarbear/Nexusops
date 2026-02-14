package main

import (
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
	"github.com/hendrix/nexusops/internal/config"
	"github.com/hendrix/nexusops/internal/middleware"
)

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		// TODO: Implement proper origin check for production
		return true
	},
}

// Client represents a connected WebSocket client
type Client struct {
	ID             string
	UserID         string
	ProjectID      string
	Conn           *websocket.Conn
	Send           chan []byte
	OpenclawConn   *websocket.Conn
	mu             sync.Mutex
}

// ChatGateway manages WebSocket connections
type ChatGateway struct {
	clients    map[string]*Client
	register   chan *Client
	unregister chan *Client
	mu         sync.RWMutex
	cfg        *config.Config
}

func NewChatGateway(cfg *config.Config) *ChatGateway {
	return &ChatGateway{
		clients:    make(map[string]*Client),
		register:   make(chan *Client, 256),
		unregister: make(chan *Client, 256),
		cfg:        cfg,
	}
}

func (g *ChatGateway) Run() {
	for {
		select {
		case client := <-g.register:
			g.mu.Lock()
			g.clients[client.ID] = client
			g.mu.Unlock()
			log.Printf("Client connected: %s", client.ID)

		case client := <-g.unregister:
			g.mu.Lock()
			if _, ok := g.clients[client.ID]; ok {
				delete(g.clients, client.ID)
				close(client.Send)
			}
			g.mu.Unlock()
			log.Printf("Client disconnected: %s", client.ID)
		}
	}
}

func (g *ChatGateway) handleWebSocket(c *gin.Context) {
	// TODO: Extract and validate JWT token
	userID := c.Query("user_id")
	projectID := c.Query("project_id")

	if userID == "" {
		c.JSON(401, gin.H{"error": "unauthorized"})
		return
	}

	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		log.Printf("WebSocket upgrade error: %v", err)
		return
	}

	client := &Client{
		ID:        generateID(),
		UserID:    userID,
		ProjectID: projectID,
		Conn:      conn,
		Send:      make(chan []byte, 256),
	}

	g.register <- client

	// Start read/write goroutines
	go g.readPump(client)
	go g.writePump(client)
}

func (g *ChatGateway) readPump(client *Client) {
	defer func() {
		g.unregister <- client
		client.Conn.Close()
	}()

	for {
		_, message, err := client.Conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("Read error: %v", err)
			}
			break
		}

		// TODO: Rate limiting
		// TODO: Message validation
		// TODO: Content sanitization

		// Forward to Openclaw
		go g.forwardToOpenclaw(client, message)
	}
}

func (g *ChatGateway) writePump(client *Client) {
	ticker := time.NewTicker(30 * time.Second)
	defer func() {
		ticker.Stop()
		client.Conn.Close()
	}()

	for {
		select {
		case message, ok := <-client.Send:
			if !ok {
				client.Conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}
			client.Conn.WriteMessage(websocket.TextMessage, message)

		case <-ticker.C:
			if err := client.Conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

func (g *ChatGateway) forwardToOpenclaw(client *Client, message []byte) {
	// TODO: Connect to Openclaw if not connected
	// TODO: Forward message with context (project_id, user_id)
	// TODO: Stream response back to client
	// TODO: Write to audit log
	// TODO: Store message in database

	log.Printf("Forwarding message to Openclaw: %s", string(message))

	// Placeholder response
	response := []byte(`{"type": "response", "content": "AI response placeholder"}`)
	client.Send <- response
}

func generateID() string {
	return time.Now().Format("20060102150405") + "-" + randomString(8)
}

func randomString(n int) string {
	const letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, n)
	for i := range b {
		b[i] = letters[time.Now().UnixNano()%int64(len(letters))]
	}
	return string(b)
}

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()
	router.Use(gin.Recovery())
	router.Use(middleware.Logger())
	router.Use(middleware.CORS())

	gateway := NewChatGateway(cfg)
	go gateway.Run()

	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "healthy", "service": "chat-gateway"})
	})

	// WebSocket endpoint
	router.GET("/ws", gateway.handleWebSocket)

	// REST API for conversation management
	api := router.Group("/api/v1")
	{
		api.GET("/conversations", getConversations)
		api.GET("/conversations/:id/messages", getMessages)
		api.POST("/conversations/:id/messages", sendMessage)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8081"
	}

	log.Printf("Chat Gateway starting on port %s", port)
	if err := router.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

func getConversations(c *gin.Context) {
	// TODO: Fetch from database
	c.JSON(200, gin.H{"conversations": []interface{}{}})
}

func getMessages(c *gin.Context) {
	// TODO: Fetch from database
	c.JSON(200, gin.H{"messages": []interface{}{}})
}

func sendMessage(c *gin.Context) {
	// TODO: Send message and return response
	c.JSON(200, gin.H{"message": "sent"})
}
