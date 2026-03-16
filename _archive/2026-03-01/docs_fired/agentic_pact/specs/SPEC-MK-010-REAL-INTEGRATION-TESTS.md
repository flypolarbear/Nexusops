# Spec: MK-010 - Real Integration Tests

## 1. Summary

创建真实外部系统集成测试，验证 NexusOps Agent 与外部系统的真实连接和操作能力。

## 2. Goals

1. 验证 K8s Agent 可以连接真实 Kubernetes 集群
2. 验证 CICD Agent 可以触发真实 Jenkins/ArgoCD 操作
3. 验证 DNS Agent 可以操作真实 DNS 记录
4. 验证 Git Agent 可以执行真实 Git 操作
5. 所有测试使用真实 API 调用，不使用 mock

## 3. Required Configurations

### 3.1 Kubernetes
```
K8S_API_SERVER=https://...
K8S_TOKEN=xxx
K8S_NAMESPACE=default
```

### 3.2 Jenkins
```
JENKINS_URL=https://...
JENKINS_USER=xxx
JENKINS_TOKEN=xxx
```

### 3.3 ArgoCD
```
ARGOCD_URL=https://...
ARGOCD_TOKEN=xxx
```

### 3.4 DNS (Aliyun)
```
ALIYUN_ACCESS_KEY_ID=xxx
ALIYUN_ACCESS_KEY_SECRET=xxx
ALIYUN_REGION=cn-hangzhou
```

### 3.5 DNS (Cloudflare)
```
CLOUDFLARE_API_TOKEN=xxx
CLOUDFLARE_ZONE_ID=xxx
```

### 3.6 Git
```
GIT_REPO_URL=https://...
GIT_TOKEN=xxx
```

## 4. Test Cases

### 4.1 K8s Integration Tests
- [ ] CT-K8S-001: List pods in namespace
- [ ] CT-K8S-002: Get pod logs
- [ ] CT-K8S-003: Describe deployment
- [ ] CT-K8S-004: Scale deployment

### 4.2 Jenkins Integration Tests
- [ ] CT-JEN-001: List jobs
- [ ] CT-JEN-002: Trigger build
- [ ] CT-JEN-003: Get build status
- [ ] CT-JEN-004: Get build logs

### 4.3 ArgoCD Integration Tests
- [ ] CT-ARGO-001: List applications
- [ ] CT-ARGO-002: Sync application
- [ ] CT-ARGO-003: Get application status

### 4.4 DNS Integration Tests
- [ ] CT-DNS-001: List DNS records
- [ ] CT-DNS-002: Create DNS record (test)
- [ ] CT-DNS-003: Delete DNS record (test)

### 4.5 Git Integration Tests
- [ ] CT-GIT-001: List branches
- [ ] CT-GIT-002: Get commit history
- [ ] CT-GIT-003: Create branch (test)
- [ ] CT-GIT-004: Delete branch (test)

## 5. Test File Structure

```
backend/tests/integration/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_k8s_real.py         # K8s real tests
├── test_jenkins_real.py     # Jenkins real tests
├── test_argocd_real.py      # ArgoCD real tests
├── test_dns_real.py         # DNS real tests
└── test_git_real.py         # Git real tests
```

## 6. Running Tests

```bash
# Run all integration tests
pytest backend/tests/integration/ -v

# Run specific integration
pytest backend/tests/integration/test_k8s_real.py -v

# Skip integration tests (for CI without credentials)
pytest backend/tests/ -v -m "not integration"
```

## 7. Security Notes

1. 所有凭证通过环境变量传入
2. 凭证不写入代码或配置文件
3. 测试完成后清理创建的测试资源
4. 使用 `.env` 文件时确保在 `.gitignore` 中
