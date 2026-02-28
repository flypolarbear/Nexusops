"""
NexusOps Adapters - Kubernetes

Adapter for Kubernetes API operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from app.adapters.base import BaseAdapter


class KubernetesAdapter(BaseAdapter):
    """
    Kubernetes API Adapter.
    
    Provides standardized methods for K8s operations.
    Each method corresponds to one or more tools.
    """
    
    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        context: Optional[str] = None
    ):
        """
        Initialize Kubernetes adapter.
        
        Args:
            kubeconfig_path: Path to kubeconfig file
            context: Kubernetes context to use
        """
        self._kubeconfig_path = kubeconfig_path
        self._context = context
        self._core_v1 = None
        self._apps_v1 = None
        self._networking_v1 = None
        self._initialized = False
        self._init_error: Optional[str] = None
    def _ensure_initialized(self):
        """Ensure K8s client is initialized"""
        if self._initialized:
            return
        
        if self._init_error:
            raise RuntimeError(f"K8s client initialization failed: {self._init_error}")
        
        try:
            self._initialize_client()
            self._initialized = True
        except Exception as e:
            self._init_error = str(e)
            raise
    
    def _initialize_client(self):
        """Initialize Kubernetes client"""
        try:
            from kubernetes import client, config
            
            if self._kubeconfig_path:
                config.load_kube_config(
                    config_file=self._kubeconfig_path,
                    context=self._context
                )
            else:
                try:
                    config.load_incluster_config()
                except Exception:
                    config.load_kube_config(context=self._context)
            
            self._core_v1 = client.CoreV1Api()
            self._apps_v1 = client.AppsV1Api()
            self._networking_v1 = client.NetworkingV1Api()
        except ImportError:
            raise RuntimeError("kubernetes package not installed. Run: pip install kubernetes")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Kubernetes client: {e}")
    
    async def health_check(self) -> bool:
        """Check connection to Kubernetes"""
        try:
            self._ensure_initialized()
            self._core_v1.list_namespace(limit=1)
            return True
        except Exception:
            return False
    
    # ============================================================
    # Pod Operations
    # ============================================================
    
    async def list_pods(
        self,
        namespace: str = "default",
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        List pods in a namespace.
        
        Args:
            namespace: Kubernetes namespace
            labels: Label selectors, e.g. {"app": "nginx"}
            
        Returns:
            Standardized result with pod list
        """
        try:
            self._ensure_initialized()
            
            label_selector = None
            if labels:
                label_selector = ",".join(f"{k}={v}" for k, v in labels.items())
            
            pods = self._core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            
            return {
                "success": True,
                "pods": [self._format_pod(p) for p in pods.items],
                "namespace": namespace,
                "total": len(pods.items)
            }
        except Exception as e:
            return self._handle_api_error(e, "list_pods")
    
    async def get_pod(self, name: str, namespace: str = "default") -> Dict[str, Any]:
        """
        Get detailed pod information.
        
        Args:
            name: Pod name
            namespace: Kubernetes namespace
            
        Returns:
            Standardized result with pod details
        """
        try:
            self._ensure_initialized()
            
            pod = self._core_v1.read_namespaced_pod(name, namespace)
            
            return {
                "success": True,
                "pod": self._format_pod_detail(pod),
                "namespace": namespace
            }
        except Exception as e:
            return self._handle_api_error(e, "get_pod", resource=name)
    
    async def delete_pod(
        self,
        name: str,
        namespace: str = "default",
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Delete a pod.
        
        Args:
            name: Pod name
            namespace: Kubernetes namespace
            force: Force deletion without grace period
            
        Returns:
            Standardized result
        """
        try:
            self._ensure_initialized()
            
            grace_period = 0 if force else None
            self._core_v1.delete_namespaced_pod(
                name=name,
                namespace=namespace,
                grace_period_seconds=grace_period
            )
            
            return {
                "success": True,
                "message": f"Pod {name} deleted from {namespace}",
                "name": name,
                "namespace": namespace
            }
        except Exception as e:
            return self._handle_api_error(e, "delete_pod", resource=name)
    
    async def get_pod_logs(
        self,
        name: str,
        namespace: str = "default",
        tail_lines: int = 100,
        container: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get pod logs.
        
        Args:
            name: Pod name
            namespace: Kubernetes namespace
            tail_lines: Number of lines to return
            container: Container name (for multi-container pods)
            
        Returns:
            Standardized result with logs
        """
        try:
            self._ensure_initialized()
            
            logs = self._core_v1.read_namespaced_pod_log(
                name=name,
                namespace=namespace,
                tail_lines=tail_lines,
                container=container
            )
            
            return {
                "success": True,
                "logs": logs,
                "name": name,
                "namespace": namespace,
                "tail_lines": tail_lines
            }
        except Exception as e:
            return self._handle_api_error(e, "get_pod_logs", resource=name)
    
    # ============================================================
    # Deployment Operations
    # ============================================================
    
    async def list_deployments(
        self,
        namespace: str = "default",
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        List deployments in a namespace.
        
        Args:
            namespace: Kubernetes namespace
            labels: Label selectors
            
        Returns:
            Standardized result with deployment list
        """
        try:
            self._ensure_initialized()
            
            label_selector = None
            if labels:
                label_selector = ",".join(f"{k}={v}" for k, v in labels.items())
            
            deployments = self._apps_v1.list_namespaced_deployment(
                namespace=namespace,
                label_selector=label_selector
            )
            
            return {
                "success": True,
                "deployments": [self._format_deployment(d) for d in deployments.items],
                "namespace": namespace,
                "total": len(deployments.items)
            }
        except Exception as e:
            return self._handle_api_error(e, "list_deployments")
    
    async def get_deployment(self, name: str, namespace: str = "default") -> Dict[str, Any]:
        """
        Get detailed deployment information.
        
        Args:
            name: Deployment name
            namespace: Kubernetes namespace
            
        Returns:
            Standardized result with deployment details
        """
        try:
            self._ensure_initialized()
            
            deployment = self._apps_v1.read_namespaced_deployment(name, namespace)
            
            return {
                "success": True,
                "deployment": self._format_deployment_detail(deployment),
                "namespace": namespace
            }
        except Exception as e:
            return self._handle_api_error(e, "get_deployment", resource=name)
    
    async def scale_deployment(
        self,
        name: str,
        replicas: int,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Scale a deployment.
        
        Args:
            name: Deployment name
            replicas: Target replica count
            namespace: Kubernetes namespace
            
        Returns:
            Standardized result
        """
        try:
            self._ensure_initialized()
            
            # Get current state
            deployment = self._apps_v1.read_namespaced_deployment(name, namespace)
            old_replicas = deployment.spec.replicas
            
            # Update replicas
            deployment.spec.replicas = replicas
            self._apps_v1.patch_namespaced_deployment(name, namespace, deployment)
            
            return {
                "success": True,
                "name": name,
                "namespace": namespace,
                "old_replicas": old_replicas,
                "new_replicas": replicas,
                "message": f"Scaled {name} from {old_replicas} to {replicas} replicas"
            }
        except Exception as e:
            return self._handle_api_error(e, "scale_deployment", resource=name)
    
    # ============================================================
    # Namespace Operations
    # ============================================================
    
    async def list_namespaces(self) -> Dict[str, Any]:
        """
        List all namespaces.
        
        Returns:
            Standardized result with namespace list
        """
        try:
            self._ensure_initialized()
            
            namespaces = self._core_v1.list_namespace()
            
            return {
                "success": True,
                "namespaces": [
                    {
                        "name": ns.metadata.name,
                        "status": ns.status.phase,
                        "age": self._get_age(ns.metadata.creation_timestamp)
                    }
                    for ns in namespaces.items
                ],
                "total": len(namespaces.items)
            }
        except Exception as e:
            return self._handle_api_error(e, "list_namespaces")
    
    # ============================================================
    # Service Operations
    # ============================================================
    
    async def list_services(
        self,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        List services in a namespace.
        
        Args:
            namespace: Kubernetes namespace
            
        Returns:
            Standardized result with service list
        """
        try:
            self._ensure_initialized()
            
            services = self._core_v1.list_namespaced_service(namespace)
            
            return {
                "success": True,
                "services": [self._format_service(s) for s in services.items],
                "namespace": namespace,
                "total": len(services.items)
            }
        except Exception as e:
            return self._handle_api_error(e, "list_services")
    
    async def get_service(self, name: str, namespace: str = "default") -> Dict[str, Any]:
        """
        Get detailed service information including access URLs.
        
        Args:
            name: Service name
            namespace: Kubernetes namespace
            
        Returns:
            Standardized result with service details
        """
        try:
            self._ensure_initialized()
            
            service = self._core_v1.read_namespaced_service(name, namespace)
            
            return {
                "success": True,
                "service": self._format_service(service),
                "namespace": namespace
            }
        except Exception as e:
            return self._handle_api_error(e, "get_service", resource=name)
    
    # ============================================================
    # Ingress Operations
    # ============================================================
    
    async def list_ingresses(self, namespace: str = "default") -> Dict[str, Any]:
        """
        List ingresses in a namespace.
        
        Args:
            namespace: Kubernetes namespace
            
        Returns:
            Standardized result with ingress list
        """
        try:
            self._ensure_initialized()
            
            ingresses = self._networking_v1.list_namespaced_ingress(namespace)
            
            return {
                "success": True,
                "ingresses": [self._format_ingress(ing) for ing in ingresses.items],
                "namespace": namespace,
                "total": len(ingresses.items)
            }
        except Exception as e:
            return self._handle_api_error(e, "list_ingresses")
    # ============================================================
    # Formatting Methods
    # ============================================================
    
    def _format_pod(self, pod) -> Dict[str, Any]:
        """Format pod summary"""
        return {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "ready": self._get_ready_status(pod),
            "restarts": self._get_restart_count(pod),
            "age": self._get_age(pod.metadata.creation_timestamp),
            "ip": pod.status.pod_ip,
            "node": pod.spec.node_name,
        }
    
    def _format_pod_detail(self, pod) -> Dict[str, Any]:
        """Format pod details"""
        return {
            **self._format_pod(pod),
            "labels": pod.metadata.labels or {},
            "annotations": pod.metadata.annotations or {},
            "containers": [
                {
                    "name": c.name,
                    "image": c.image,
                    "ports": [p.container_port for p in (c.ports or [])],
                    "resources": self._format_resources(c.resources),
                }
                for c in pod.spec.containers
            ],
            "volumes": [v.name for v in (pod.spec.volumes or [])],
            "created": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
        }
    
    def _format_deployment(self, deployment) -> Dict[str, Any]:
        """Format deployment summary"""
        return {
            "name": deployment.metadata.name,
            "namespace": deployment.metadata.namespace,
            "replicas": deployment.spec.replicas,
            "ready": deployment.status.ready_replicas or 0,
            "available": deployment.status.available_replicas or 0,
            "updated": deployment.status.updated_replicas or 0,
            "age": self._get_age(deployment.metadata.creation_timestamp),
        }
    
    def _format_deployment_detail(self, deployment) -> Dict[str, Any]:
        """Format deployment details"""
        return {
            **self._format_deployment(deployment),
            "labels": deployment.metadata.labels or {},
            "selector": deployment.spec.selector.match_labels if deployment.spec.selector else {},
            "strategy": deployment.spec.strategy.type if deployment.spec.strategy else None,
            "containers": [
                {
                    "name": c.name,
                    "image": c.image,
                }
                for c in (deployment.spec.template.spec.containers if deployment.spec.template else [])
            ],
        }
    
    def _format_service(self, service) -> Dict[str, Any]:
        """Format service summary with access URL info"""
        service_type = service.spec.type
        
        # Build ports array with node_port if available
        ports = []
        for p in (service.spec.ports or []):
            port_info = {
                "port": p.port,
                "target_port": p.target_port,
                "protocol": p.protocol,
            }
            # Add node_port for NodePort type
            if service_type == "NodePort" and p.node_port:
                port_info["node_port"] = p.node_port
            ports.append(port_info)
        
        # Get external IPs based on service type
        external_ips = []
        loadbalancer_ip = None
        
        if service_type == "LoadBalancer":
            # Get LoadBalancer external IP
            if service.status.loadBalancer and service.status.loadBalancer.ingress:
                for ingress in service.status.loadBalancer.ingress:
                    if ingress.ip:
                        external_ips.append(ingress.ip)
                        loadbalancer_ip = ingress.ip
                    if ingress.hostname:
                        external_ips.append(ingress.hostname)
        elif service_type == "NodePort":
            # Get node external IPs if available
            if service.spec.externalIPs:
                external_ips.extend(service.spec.externalIPs)
        
        # Build access URLs
        access_urls = self._build_access_urls(service, ports, external_ips, loadbalancer_ip)
        
        return {
            "name": service.metadata.name,
            "namespace": service.metadata.namespace,
            "type": service_type,
            "cluster_ip": service.spec.cluster_ip,
            "ports": ports,
            "external_ips": external_ips,
            "loadbalancer_ip": loadbalancer_ip,
            "access_urls": access_urls,
            "age": self._get_age(service.metadata.creation_timestamp),
        }
    
    def _build_access_urls(
        self,
        service,
        ports: List[Dict],
        external_ips: List[str],
        loadbalancer_ip: Optional[str]
    ) -> List[str]:
        """Build access URLs based on service type"""
        urls = []
        service_type = service.spec.type
        namespace = service.metadata.namespace
        name = service.metadata.name
        
        for port_info in ports:
            port = port_info["port"]
            
            # Determine URL scheme
            scheme = "https" if port in [443, 8443] else "http"
            
            if service_type == "LoadBalancer":
                # LoadBalancer - use external IP
                if loadbalancer_ip:
                    url_port = f":{port}" if port not in [80, 443] else ""
                    urls.append(f"{scheme}://{loadbalancer_ip}{url_port}")
                for ip in external_ips:
                    if ip != loadbalancer_ip:
                        url_port = f":{port}" if port not in [80, 443] else ""
                        urls.append(f"{scheme}://{ip}{url_port}")
            
            elif service_type == "NodePort":
                # NodePort - need node IP + node_port
                node_port = port_info.get("node_port")
                if node_port:
                    # Indicate that node IP is needed
                    urls.append(f"{scheme}://<node-ip>:{node_port}")
            
            elif service_type == "ClusterIP":
                # ClusterIP - internal only
                cluster_ip = service.spec.cluster_ip
                if cluster_ip and cluster_ip != "None":
                    url_port = f":{port}" if port not in [80, 443] else ""
                    urls.append(f"{scheme}://{cluster_ip}{url_port} (internal only)")
        
        # Add note about port-forward for internal access
        if service_type == "ClusterIP":
            first_port = ports[0]["port"] if ports else 80
            urls.append(f"kubectl port-forward svc/{name} -n {namespace} <local-port>:{first_port}")
        
        return urls
    
    def _format_ingress(self, ingress) -> Dict[str, Any]:
        """Format ingress summary"""
        # Build hosts and paths
        hosts = []
        paths = []
        
        if ingress.spec.rules:
            for rule in ingress.spec.rules:
                host = rule.host or "*"
                hosts.append(host)
                
                if rule.http and rule.http.paths:
                    for path in rule.http.paths:
                        backend = path.backend
                        service_name = None
                        service_port = None
                        
                        # Handle different backend types
                        if backend.service:
                            service_name = backend.service.name
                            service_port = backend.service.port.number if backend.service.port else None
                        
                        paths.append({
                            "host": host,
                            "path": path.path or "/",
                            "path_type": path.path_type or "Prefix",
                            "service_name": service_name,
                            "service_port": service_port,
                        })
        
        # Build TLS info
        tls = []
        if ingress.spec.tls:
            for t in ingress.spec.tls:
                tls.append({
                    "hosts": t.hosts or [],
                    "secret_name": t.secret_name,
                })
        
        # Build access URLs
        access_urls = []
        for host in hosts:
            scheme = "https" if any(t["hosts"] and host in t["hosts"] for t in tls) else "http"
            if host != "*":
                access_urls.append(f"{scheme}://{host}")
        
        return {
            "name": ingress.metadata.name,
            "namespace": ingress.metadata.namespace,
            "hosts": hosts,
            "paths": paths,
            "tls": tls,
            "access_urls": access_urls,
            "age": self._get_age(ingress.metadata.creation_timestamp),
        }
    
    def _format_resources(self, resources) -> Dict[str, Any]:
        """Format resource requirements"""
        if not resources:
            return {}
        return {
            "requests": dict(resources.requests) if resources.requests else {},
            "limits": dict(resources.limits) if resources.limits else {},
        }
    
    # ============================================================
    # Utility Methods
    # ============================================================
    
    def _get_ready_status(self, pod) -> str:
        """Get pod ready status as 'ready/total'"""
        if not pod.status.container_statuses:
            return "0/0"
        ready = sum(1 for c in pod.status.container_statuses if c.ready)
        total = len(pod.status.container_statuses)
        return f"{ready}/{total}"
    
    def _get_restart_count(self, pod) -> int:
        """Get total restart count"""
        if not pod.status.container_statuses:
            return 0
        return sum(c.restart_count for c in pod.status.container_statuses)
    
    def _get_age(self, creation_timestamp) -> str:
        """Calculate resource age"""
        if not creation_timestamp:
            return "unknown"
        
        try:
            created = creation_timestamp.replace(tzinfo=None)
            age = datetime.utcnow() - created
            
            if age.days > 365:
                years = age.days // 365
                return f"{years}y"
            elif age.days > 30:
                months = age.days // 30
                return f"{months}M"
            elif age.days > 0:
                return f"{age.days}d"
            elif age.seconds >= 3600:
                hours = age.seconds // 3600
                return f"{hours}h"
            elif age.seconds >= 60:
                minutes = age.seconds // 60
                return f"{minutes}m"
            else:
                return f"{age.seconds}s"
        except Exception:
            return "unknown"
    
    def _handle_api_error(
        self, 
        error: Exception, 
        operation: str,
        resource: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle Kubernetes API errors"""
        error_str = str(error)
        code = "API_ERROR"
        
        # Check for common error types
        if "404" in error_str or "Not Found" in error_str:
            code = "NOT_FOUND"
            error_str = f"Resource not found: {resource}" if resource else "Resource not found"
        elif "403" in error_str or "Forbidden" in error_str:
            code = "FORBIDDEN"
            error_str = "Permission denied"
        elif "401" in error_str or "Unauthorized" in error_str:
            code = "UNAUTHORIZED"
            error_str = "Authentication failed"
        elif "timeout" in error_str.lower():
            code = "TIMEOUT"
        
        return {
            "success": False,
            "error": error_str,
            "code": code,
            "operation": operation,
            "resource": resource
        }
