package models

import (
	"time"

	"github.com/google/uuid"
)

// Project represents a business/product line
type Project struct {
	ID          uuid.UUID `json:"id" db:"id"`
	Name        string    `json:"name" db:"name"`
	Description string    `json:"description" db:"description"`
	OwnerID     uuid.UUID `json:"owner_id" db:"owner_id"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
}

// Region represents a geographic region
type Region struct {
	ID        uuid.UUID `json:"id" db:"id"`
	Name      string    `json:"name" db:"name"`
	Code      string    `json:"code" db:"code"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
}

// Cluster represents a Kubernetes cluster
type Cluster struct {
	ID          uuid.UUID `json:"id" db:"id"`
	Name        string    `json:"name" db:"name"`
	RegionID    uuid.UUID `json:"region_id" db:"region_id"`
	Provider    string    `json:"provider" db:"provider"`
	Endpoint    string    `json:"endpoint" db:"endpoint"`
	Status      string    `json:"status" db:"status"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
}

// Namespace represents a K8s namespace
type Namespace struct {
	ID        uuid.UUID `json:"id" db:"id"`
	Name      string    `json:"name" db:"name"`
	ClusterID uuid.UUID `json:"cluster_id" db:"cluster_id"`
	ProjectID uuid.UUID `json:"project_id" db:"project_id"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
}

// Service represents a deployed service
type Service struct {
	ID          uuid.UUID `json:"id" db:"id"`
	Name        string    `json:"name" db:"name"`
	NamespaceID uuid.UUID `json:"namespace_id" db:"namespace_id"`
	ProjectID   uuid.UUID `json:"project_id" db:"project_id"`
	Replicas    int       `json:"replicas" db:"replicas"`
	Status      string    `json:"status" db:"status"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
}

// Build represents a Jenkins build
type Build struct {
	ID          uuid.UUID `json:"id" db:"id"`
	JobName     string    `json:"job_name" db:"job_name"`
	BuildNumber int       `json:"build_number" db:"build_number"`
	Status      string    `json:"status" db:"status"`
	CommitSHA   string    `json:"commit_sha" db:"commit_sha"`
	Branch      string    `json:"branch" db:"branch"`
	Duration    int64     `json:"duration" db:"duration"`
	StartedAt   time.Time `json:"started_at" db:"started_at"`
	FinishedAt  *time.Time `json:"finished_at" db:"finished_at"`
}

// Image represents a Harbor image
type Image struct {
	ID           uuid.UUID `json:"id" db:"id"`
	Registry     string    `json:"registry" db:"registry"`
	Repository   string    `json:"repository" db:"repository"`
	Tag          string    `json:"tag" db:"tag"`
	Digest       string    `json:"digest" db:"digest"`
	BuildID      *uuid.UUID `json:"build_id" db:"build_id"`
	CreatedAt    time.Time `json:"created_at" db:"created_at"`
	PushedAt     time.Time `json:"pushed_at" db:"pushed_at"`
	Size         int64     `json:"size" db:"size"`
	Vulnerabilities int    `json:"vulnerabilities" db:"vulnerabilities"`
}

// Deployment represents an ArgoCD deployment
type Deployment struct {
	ID           uuid.UUID `json:"id" db:"id"`
	ServiceID    uuid.UUID `json:"service_id" db:"service_id"`
	ImageID      uuid.UUID `json:"image_id" db:"image_id"`
	ArgoCDApp    string    `json:"argocd_app" db:"argocd_app"`
	SyncStatus   string    `json:"sync_status" db:"sync_status"`
	HealthStatus string    `json:"health_status" db:"health_status"`
	Revision     string    `json:"revision" db:"revision"`
	DeployedAt   time.Time `json:"deployed_at" db:"deployed_at"`
	DeployedBy   uuid.UUID `json:"deployed_by" db:"deployed_by"`
}

// Alert represents a monitoring alert
type Alert struct {
	ID          uuid.UUID `json:"id" db:"id"`
	Source      string    `json:"source" db:"source"`
	AlertName   string    `json:"alert_name" db:"alert_name"`
	Severity    string    `json:"severity" db:"severity"`
	Status      string    `json:"status" db:"status"`
	ServiceID   *uuid.UUID `json:"service_id" db:"service_id"`
	ProjectID   *uuid.UUID `json:"project_id" db:"project_id"`
	Summary     string    `json:"summary" db:"summary"`
	Description string    `json:"description" db:"description"`
	Labels      JSONB     `json:"labels" db:"labels"`
	FiredAt     time.Time `json:"fired_at" db:"fired_at"`
	ResolvedAt  *time.Time `json:"resolved_at" db:"resolved_at"`
}

// JSONB for PostgreSQL JSONB type
type JSONB map[string]interface{}

// Ticket represents a support/issue ticket
type Ticket struct {
	ID          uuid.UUID `json:"id" db:"id"`
	Title       string    `json:"title" db:"title"`
	Description string    `json:"description" db:"description"`
	Type        string    `json:"type" db:"type"` // request, bug, change, vendor_task
	Status      string    `json:"status" db:"status"`
	Priority    string    `json:"priority" db:"priority"`
	ProjectID   uuid.UUID `json:"project_id" db:"project_id"`
	ReporterID  uuid.UUID `json:"reporter_id" db:"reporter_id"`
	AssigneeID  *uuid.UUID `json:"assignee_id" db:"assignee_id"`
	ExternalID  string    `json:"external_id" db:"external_id"`
	ExternalURL string    `json:"external_url" db:"external_url"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
	ResolvedAt  *time.Time `json:"resolved_at" db:"resolved_at"`
}

// User represents a platform user
type User struct {
	ID        uuid.UUID `json:"id" db:"id"`
	Username  string    `json:"username" db:"username"`
	Email     string    `json:"email" db:"email"`
	FullName  string    `json:"full_name" db:"full_name"`
	Role      string    `json:"role" db:"role"` // admin, internal, vendor
	IsActive  bool      `json:"is_active" db:"is_active"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
	UpdatedAt time.Time `json:"updated_at" db:"updated_at"`
}

// Vendor represents an external vendor/contractor
type Vendor struct {
	ID          uuid.UUID `json:"id" db:"id"`
	Name        string    `json:"name" db:"name"`
	Contact     string    `json:"contact" db:"contact"`
	Description string    `json:"description" db:"description"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
}

// Conversation represents an AI chat conversation
type Conversation struct {
	ID        uuid.UUID `json:"id" db:"id"`
	ProjectID *uuid.UUID `json:"project_id" db:"project_id"`
	AgentID   string    `json:"agent_id" db:"agent_id"`
	UserID    uuid.UUID `json:"user_id" db:"user_id"`
	Title     string    `json:"title" db:"title"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
	UpdatedAt time.Time `json:"updated_at" db:"updated_at"`
}

// Message represents a chat message
type Message struct {
	ID             uuid.UUID `json:"id" db:"id"`
	ConversationID uuid.UUID `json:"conversation_id" db:"conversation_id"`
	Role           string    `json:"role" db:"role"` // user, assistant, system
	Content        string    `json:"content" db:"content"`
	CreatedAt      time.Time `json:"created_at" db:"created_at"`
}

// Attachment represents a file attachment
type Attachment struct {
	ID             uuid.UUID `json:"id" db:"id"`
	ConversationID uuid.UUID `json:"conversation_id" db:"conversation_id"`
	MessageID      *uuid.UUID `json:"message_id" db:"message_id"`
	Filename       string    `json:"filename" db:"filename"`
	URL            string    `json:"url" db:"url"`
	Size           int64     `json:"size" db:"size"`
	MimeType       string    `json:"mime_type" db:"mime_type"`
	CreatedAt      time.Time `json:"created_at" db:"created_at"`
}

// AuditLog represents an audit log entry
type AuditLog struct {
	ID        uuid.UUID `json:"id" db:"id"`
	ActorID   uuid.UUID `json:"actor_id" db:"actor_id"`
	Action    string    `json:"action" db:"action"`
	Target    string    `json:"target" db:"target"`
	Details   JSONB     `json:"details" db:"details"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
}
