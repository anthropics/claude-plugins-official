# Skill: OpenAPI/Swagger TypeScript Client 生成

从 Swagger/OpenAPI 规范自动生成 TypeScript API 客户端，包括类型定义、fetch/axios 客户端、React Query hooks、SWR hooks。

## 触发条件

当用户请求以下操作时激活：
- "生成 api client"、"generate api client"、"从 swagger 生成客户端"
- "openapi client"、"swagger client"、"生成 ts 客户端"
- "从 openapi 生成类型"、"generate types from swagger"

---

## 执行步骤

### 第一步：获取 OpenAPI Spec

根据用户提供的输入方式获取 spec：

**方式 A：URL**
```bash
# 直接下载 spec
curl -s "<URL>" -o /tmp/openapi-spec.json

# 常见 swagger 端点
curl -s "http://localhost:3000/api-docs" -o /tmp/openapi-spec.json
curl -s "http://localhost:3000/swagger.json" -o /tmp/openapi-spec.json
curl -s "http://localhost:8080/v3/api-docs" -o /tmp/openapi-spec.json  # Spring Boot
curl -s "http://localhost:8000/openapi.json" -o /tmp/openapi-spec.json  # FastAPI
```

**方式 B：文件路径**
```bash
# 查找项目中的 spec 文件
find . -name "openapi.*" -o -name "swagger.*" -o -name "api-docs.*" | grep -v node_modules
ls docs/openapi.* docs/swagger.* 2>/dev/null
```

直接读取用户指定的文件路径（支持 `.json`、`.yaml`、`.yml`）。

**方式 C：粘贴内容**

用户直接粘贴 YAML/JSON 内容时，保存到临时文件后继续。

**Spec 验证：**
```bash
# 验证 spec 格式是否有效
bunx @apidevtools/swagger-cli validate /tmp/openapi-spec.json 2>&1
```

若验证失败，报告具体错误并停止。

### 第二步：解析 Spec 结构

读取 spec 文件，提取以下关键信息：

1. **基础信息** — `info.title`、`info.version`、`servers[].url`
2. **认证方式** — `components.securitySchemes`（Bearer / API Key / Cookie / OAuth2）
3. **所有端点** — `paths` 下的每个 path + method 组合
4. **Schema 定义** — `components.schemas` 下的所有类型
5. **全局配置** — 公共参数、全局 security 要求

**提取端点信息清单：**
- HTTP method + path
- operationId（用于函数命名）
- parameters（path / query / header）
- requestBody schema
- responses（所有 status code + schema）
- tags（用于文件分组）
- security requirements

### 第三步：读取项目代码风格配置

```bash
# 检测项目配置
cat tsconfig.json 2>/dev/null | head -50
cat .eslintrc.json .eslintrc.js .eslintrc.yml 2>/dev/null | head -30
cat .prettierrc .prettierrc.json .prettierrc.js 2>/dev/null | head -20
cat biome.json 2>/dev/null | head -30

# 检测包管理器和现有依赖
cat package.json 2>/dev/null | grep -E "(axios|@tanstack/react-query|swr|ky|got|ofetch)"
```

**适配规则：**

| 项目配置 | 生成代码适配 |
|---------|------------|
| `tsconfig.json` 有 `strict: true` | 生成严格类型，不使用 `any` |
| `tsconfig.json` 有 `paths` 别名 | import 使用对应别名 |
| ESLint 使用 single quotes | 生成代码使用单引号 |
| ESLint 禁止分号 | 生成代码不加分号 |
| Prettier 配置 `tabWidth: 4` | 使用 4 空格缩进 |
| 项目已有 axios | 默认生成 axios 客户端 |
| 项目已有 @tanstack/react-query | 自动生成 React Query hooks |
| 项目已有 swr | 自动生成 SWR hooks |

**默认代码风格（无配置时）：**
- 单引号、无分号、2 空格缩进
- 使用 `const` + 箭头函数
- async/await 风格

### 第四步：生成 TypeScript 类型定义

#### OpenAPI → TypeScript 类型映射表

| OpenAPI Type | OpenAPI Format | TypeScript Type |
|-------------|---------------|-----------------|
| `string` | — | `string` |
| `string` | `date` | `string` |
| `string` | `date-time` | `string` |
| `string` | `email` | `string` |
| `string` | `uri` / `url` | `string` |
| `string` | `uuid` | `string` |
| `string` | `binary` | `File \| Blob` |
| `string` | `byte` | `string` |
| `string` + `enum` | — | 字面量联合类型 `'a' \| 'b' \| 'c'` |
| `number` | — | `number` |
| `number` | `float` / `double` | `number` |
| `integer` | — | `number` |
| `integer` | `int32` / `int64` | `number` |
| `boolean` | — | `boolean` |
| `array` | — | `T[]`（T 为 items 类型） |
| `object` | — | 生成 interface |
| `object` + `additionalProperties` | — | `Record<string, T>` |
| `$ref` | — | 引用对应 interface 名称 |
| `oneOf` | — | `A \| B` 联合类型 |
| `allOf` | — | `A & B` 交叉类型 |
| `anyOf` | — | `A \| B` 联合类型 |
| `nullable: true` | — | `T \| null` |

#### 类型生成规则

1. **Schema 名称** → interface 名称，PascalCase
2. **属性名** → 保持 spec 原样（通常 camelCase）
3. **required 字段** → 非可选属性
4. **非 required 字段** → 可选属性 `prop?: Type`
5. **枚举** → 导出为 `type` 字面量联合 + `const` 枚举数组
6. **嵌套对象** → 提取为独立 interface
7. **循环引用** → 使用 interface 名称引用（TypeScript 天然支持）

**类型生成模板：**

```typescript
// --- types.ts ---

/** User entity */
export interface User {
  id: string
  name: string
  email: string
  role: UserRole
  createdAt: string
  avatar?: string | null
}

/** User role enum */
export type UserRole = 'admin' | 'user' | 'guest'
export const USER_ROLES = ['admin', 'user', 'guest'] as const

/** Create user request */
export interface CreateUserRequest {
  name: string
  email: string
  role?: UserRole
}

/** Paginated response wrapper */
export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
}

/** API error response */
export interface ApiError {
  message: string
  code: string
  details?: Record<string, string[]>
}
```

### 第五步：生成 API 客户端

询问用户偏好（或根据项目依赖自动检测）：
- **fetch**（零依赖，默认）
- **axios**（如项目已安装 axios）

#### Fetch Client 模板

```typescript
// --- client.ts ---

export interface ClientConfig {
  baseUrl: string
  headers?: Record<string, string>
  /** Authentication token or token getter */
  getToken?: () => string | Promise<string> | null
  /** API key for x-api-key header */
  apiKey?: string
  /** Request timeout in ms (default: 30000) */
  timeout?: number
  /** Retry count for failed requests (default: 0) */
  retries?: number
  /** Retry delay in ms (default: 1000) */
  retryDelay?: number
  /** Request/response interceptors */
  onRequest?: (url: string, init: RequestInit) => RequestInit | Promise<RequestInit>
  onResponse?: (response: Response) => Response | Promise<Response>
  onError?: (error: ApiClientError) => void
}

export class ApiClientError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly body: unknown,
    public readonly url: string,
    public readonly method: string
  ) {
    super(message)
    this.name = 'ApiClientError'
  }
}

const createClient = (config: ClientConfig) => {
  const { baseUrl, timeout = 30000, retries = 0, retryDelay = 1000 } = config

  const request = async <T>(
    method: string,
    path: string,
    options: {
      params?: Record<string, string | number | boolean | undefined>
      body?: unknown
      headers?: Record<string, string>
    } = {}
  ): Promise<T> => {
    // Build URL with query params
    const url = new URL(path, baseUrl)
    if (options.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.set(key, String(value))
        }
      })
    }

    // Build headers
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...config.headers,
      ...options.headers,
    }

    // Authentication
    if (config.getToken) {
      const token = await config.getToken()
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
    }
    if (config.apiKey) {
      headers['X-API-Key'] = config.apiKey
    }

    let init: RequestInit = {
      method,
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: AbortSignal.timeout(timeout),
    }

    // Request interceptor
    if (config.onRequest) {
      init = await config.onRequest(url.toString(), init)
    }

    // Retry logic
    let lastError: Error | null = null
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        let response = await fetch(url.toString(), init)

        // Response interceptor
        if (config.onResponse) {
          response = await config.onResponse(response)
        }

        if (!response.ok) {
          const body = await response.json().catch(() => null)
          const error = new ApiClientError(
            `${method} ${path} failed with status ${response.status}`,
            response.status,
            body,
            url.toString(),
            method
          )
          if (config.onError) {
            config.onError(error)
          }
          throw error
        }

        // Handle 204 No Content
        if (response.status === 204) {
          return undefined as T
        }

        return (await response.json()) as T
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error))

        // Only retry on network errors or 5xx, not on 4xx
        const isRetryable =
          !(error instanceof ApiClientError) ||
          error.status >= 500

        if (attempt < retries && isRetryable) {
          await new Promise((resolve) => setTimeout(resolve, retryDelay * (attempt + 1)))
          continue
        }

        throw lastError
      }
    }

    throw lastError
  }

  return { request }
}
```

#### Axios Client 模板

```typescript
// --- client.ts (axios version) ---

import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

export interface ClientConfig {
  baseUrl: string
  headers?: Record<string, string>
  getToken?: () => string | Promise<string> | null
  apiKey?: string
  timeout?: number
  retries?: number
  retryDelay?: number
}

export class ApiClientError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly body: unknown,
    public readonly url: string,
    public readonly method: string
  ) {
    super(message)
    this.name = 'ApiClientError'
  }
}

const createClient = (config: ClientConfig): AxiosInstance => {
  const { baseUrl, timeout = 30000, retries = 0, retryDelay = 1000 } = config

  const instance = axios.create({
    baseURL: baseUrl,
    timeout,
    headers: config.headers,
  })

  // Request interceptor: auth
  instance.interceptors.request.use(async (reqConfig) => {
    if (config.getToken) {
      const token = await config.getToken()
      if (token) {
        reqConfig.headers.Authorization = `Bearer ${token}`
      }
    }
    if (config.apiKey) {
      reqConfig.headers['X-API-Key'] = config.apiKey
    }
    return reqConfig
  })

  // Response interceptor: retry + error transform
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const reqConfig = error.config as AxiosRequestConfig & { _retryCount?: number }
      const retryCount = reqConfig._retryCount ?? 0
      const status = error.response?.status ?? 0

      if (retryCount < retries && status >= 500) {
        reqConfig._retryCount = retryCount + 1
        await new Promise((r) => setTimeout(r, retryDelay * (retryCount + 1)))
        return instance.request(reqConfig)
      }

      throw new ApiClientError(
        error.message,
        status,
        error.response?.data,
        reqConfig.url ?? '',
        reqConfig.method ?? ''
      )
    }
  )

  return instance
}
```

#### API 函数生成模板

对每个 operationId 生成一个函数：

```typescript
// --- api/users.ts ---

import type { User, CreateUserRequest, PaginatedResponse } from '../types'

// operationId → function name (camelCase)
// tag → file grouping

/** List all users */
export const listUsers = (
  client: ReturnType<typeof createClient>,
  params?: { page?: number; limit?: number; search?: string }
): Promise<PaginatedResponse<User>> =>
  client.request('GET', '/api/users', { params })

/** Get user by ID */
export const getUserById = (
  client: ReturnType<typeof createClient>,
  userId: string
): Promise<User> =>
  client.request('GET', `/api/users/${userId}`)

/** Create a new user */
export const createUser = (
  client: ReturnType<typeof createClient>,
  data: CreateUserRequest
): Promise<User> =>
  client.request('POST', '/api/users', { body: data })

/** Update user */
export const updateUser = (
  client: ReturnType<typeof createClient>,
  userId: string,
  data: Partial<CreateUserRequest>
): Promise<User> =>
  client.request('PUT', `/api/users/${userId}`, { body: data })

/** Delete user */
export const deleteUser = (
  client: ReturnType<typeof createClient>,
  userId: string
): Promise<void> =>
  client.request('DELETE', `/api/users/${userId}`)
```

**函数命名规则：**
1. 优先使用 `operationId`（转为 camelCase）
2. 若无 operationId，使用 `{method}{PathSegments}` 格式：
   - `GET /api/users` → `getApiUsers`
   - `POST /api/users/{id}/orders` → `postApiUsersOrders`
3. 路径参数（`{id}`、`{userId}`）从路径中去除，作为函数参数

### 第六步：生成 React Query Hooks（可选）

仅当项目已安装 `@tanstack/react-query` 或用户明确要求时生成。

**hooks 生成规则：**
- `GET` → `useQuery` hook
- `POST` / `PUT` / `PATCH` / `DELETE` → `useMutation` hook
- 自动推断 query key 结构
- 支持 `enabled`、`staleTime` 等配置透传

```typescript
// --- hooks/useUsers.ts ---

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from '@tanstack/react-query'
import type { User, CreateUserRequest, PaginatedResponse, ApiError } from '../types'
import { listUsers, getUserById, createUser, updateUser, deleteUser } from '../api/users'

// Query key factory
export const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (params?: { page?: number; limit?: number; search?: string }) =>
    [...userKeys.lists(), params] as const,
  details: () => [...userKeys.all, 'detail'] as const,
  detail: (id: string) => [...userKeys.details(), id] as const,
}

/** Hook: list users */
export const useListUsers = (
  params?: { page?: number; limit?: number; search?: string },
  options?: Omit<UseQueryOptions<PaginatedResponse<User>, ApiError>, 'queryKey' | 'queryFn'>
) =>
  useQuery({
    queryKey: userKeys.list(params),
    queryFn: () => listUsers(client, params),
    ...options,
  })

/** Hook: get user by ID */
export const useGetUser = (
  userId: string,
  options?: Omit<UseQueryOptions<User, ApiError>, 'queryKey' | 'queryFn'>
) =>
  useQuery({
    queryKey: userKeys.detail(userId),
    queryFn: () => getUserById(client, userId),
    enabled: !!userId,
    ...options,
  })

/** Hook: create user */
export const useCreateUser = (
  options?: UseMutationOptions<User, ApiError, CreateUserRequest>
) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateUserRequest) => createUser(client, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() })
    },
    ...options,
  })
}

/** Hook: update user */
export const useUpdateUser = (
  userId: string,
  options?: UseMutationOptions<User, ApiError, Partial<CreateUserRequest>>
) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<CreateUserRequest>) => updateUser(client, userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.detail(userId) })
      queryClient.invalidateQueries({ queryKey: userKeys.lists() })
    },
    ...options,
  })
}

/** Hook: delete user */
export const useDeleteUser = (
  options?: UseMutationOptions<void, ApiError, string>
) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) => deleteUser(client, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all })
    },
    ...options,
  })
}
```

### 第七步：生成 SWR Hooks（可选）

仅当项目已安装 `swr` 或用户明确要求时生成。

```typescript
// --- hooks/useUsers.swr.ts ---

import useSWR, { type SWRConfiguration } from 'swr'
import useSWRMutation from 'swr/mutation'
import type { User, CreateUserRequest, PaginatedResponse, ApiError } from '../types'
import { listUsers, getUserById, createUser, updateUser, deleteUser } from '../api/users'

/** SWR Hook: list users */
export const useListUsers = (
  params?: { page?: number; limit?: number; search?: string },
  config?: SWRConfiguration<PaginatedResponse<User>, ApiError>
) =>
  useSWR(
    ['users', 'list', params],
    () => listUsers(client, params),
    config
  )

/** SWR Hook: get user by ID */
export const useGetUser = (
  userId: string | undefined,
  config?: SWRConfiguration<User, ApiError>
) =>
  useSWR(
    userId ? ['users', 'detail', userId] : null,
    () => getUserById(client, userId!),
    config
  )

/** SWR Mutation Hook: create user */
export const useCreateUser = () =>
  useSWRMutation(
    ['users', 'list'],
    (_key: string[], { arg }: { arg: CreateUserRequest }) => createUser(client, arg)
  )
```

### 第八步：生成认证处理

根据 spec 中的 `securitySchemes` 生成对应认证配置：

**Bearer Token（JWT）：**
```typescript
const client = createClient({
  baseUrl: 'https://api.example.com',
  getToken: () => localStorage.getItem('access_token'),
})
```

**API Key：**
```typescript
const client = createClient({
  baseUrl: 'https://api.example.com',
  apiKey: process.env.API_KEY,
})
```

**Cookie（Session）：**
```typescript
// fetch client needs credentials: 'include'
const client = createClient({
  baseUrl: 'https://api.example.com',
  // Modify the onRequest interceptor to add credentials
  onRequest: (url, init) => ({
    ...init,
    credentials: 'include' as RequestCredentials,
  }),
})
```

**OAuth2：**
```typescript
const client = createClient({
  baseUrl: 'https://api.example.com',
  getToken: async () => {
    // Check if token is expired and refresh if needed
    const token = getStoredToken()
    if (isExpired(token)) {
      const refreshed = await refreshToken(token.refreshToken)
      storeToken(refreshed)
      return refreshed.accessToken
    }
    return token.accessToken
  },
})
```

### 第九步：组织输出文件

**默认输出目录结构：**

```
src/api-client/           # 或用户指定的目录
  ├── index.ts            # 统一导出入口
  ├── client.ts           # HTTP 客户端（fetch 或 axios）
  ├── types.ts            # 所有 TypeScript 类型/接口
  ├── api/                # API 函数，按 tag 分文件
  │   ├── users.ts
  │   ├── orders.ts
  │   └── auth.ts
  └── hooks/              # React Query / SWR hooks（可选）
      ├── useUsers.ts
      ├── useOrders.ts
      └── useAuth.ts
```

**index.ts 统一导出：**

```typescript
// --- index.ts ---

// Client
export { createClient, type ClientConfig, ApiClientError } from './client'

// Types
export type { User, CreateUserRequest, PaginatedResponse, ApiError } from './types'

// API functions
export * from './api/users'
export * from './api/orders'
export * from './api/auth'

// Hooks (if generated)
export * from './hooks/useUsers'
export * from './hooks/useOrders'
export * from './hooks/useAuth'
```

**文件分组规则：**
- 按 OpenAPI `tags` 分组，一个 tag 对应一个 API 文件和一个 hooks 文件
- 无 tag 的端点归入 `api/default.ts`
- 类型全部集中在 `types.ts`（若类型超过 500 行，按 tag 拆分到 `types/` 目录）

### 第十步：验证生成结果

```bash
# TypeScript 类型检查
bunx tsc --noEmit --strict src/api-client/**/*.ts 2>&1

# 如有 ESLint，检查代码风格
bunx eslint src/api-client/ 2>&1

# 如有 Prettier，格式化
bunx prettier --write src/api-client/ 2>&1
```

若类型检查失败，修复后重新验证。

---

## 认证方式处理汇总

| SecurityScheme Type | 处理方式 |
|--------------------|---------|
| `http` + `bearer` | `Authorization: Bearer <token>` header，通过 `getToken` 配置 |
| `apiKey` + `header` | 自定义 header（如 `X-API-Key`），通过 `apiKey` 配置 |
| `apiKey` + `query` | 将 key 追加到 URL query params |
| `apiKey` + `cookie` | `credentials: 'include'`，cookie 由浏览器自动发送 |
| `oauth2` | 同 bearer，但额外生成 token refresh 逻辑 |
| `openIdConnect` | 同 oauth2 处理 |

---

## 特殊情况处理

### 文件上传端点

当 requestBody 的 content-type 为 `multipart/form-data` 时：

```typescript
export const uploadAvatar = (
  client: ReturnType<typeof createClient>,
  userId: string,
  file: File
): Promise<{ url: string }> => {
  const formData = new FormData()
  formData.append('file', file)

  return client.request('POST', `/api/users/${userId}/avatar`, {
    body: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
```

注意：使用 FormData 时不要 JSON.stringify body，且让浏览器自动设置 Content-Type boundary。

### 下载端点

当 response 的 content-type 为 `application/octet-stream` 或 `application/pdf` 时：

```typescript
export const downloadReport = (
  client: ReturnType<typeof createClient>,
  reportId: string
): Promise<Blob> =>
  client.requestBlob('GET', `/api/reports/${reportId}/download`)
```

### 带路径参数的 URL

路径参数使用模板字符串替换：
- `/api/users/{userId}/orders/{orderId}` → `` `/api/users/${userId}/orders/${orderId}` ``
- 参数类型从 spec 的 `parameters` 中提取

### 可选 query 参数

过滤掉 `undefined` 值，不发送空参数：

```typescript
// params: { page?: number; search?: string }
// 只发送有值的参数
Object.entries(params).forEach(([key, value]) => {
  if (value !== undefined) {
    url.searchParams.set(key, String(value))
  }
})
```

---

## 质量检查清单

生成完成后，自检以下项目：

- [ ] 所有 spec 中的 schema 都已转为 TypeScript interface
- [ ] 所有端点都有对应的 API 函数
- [ ] 函数参数类型与 spec 中的 parameters + requestBody 匹配
- [ ] 返回值类型与 spec 中的 responses.200 schema 匹配
- [ ] 枚举值已生成为字面量联合类型
- [ ] 可选字段使用 `?` 标记
- [ ] nullable 字段使用 `| null` 标记
- [ ] 认证方式与 spec 的 securitySchemes 一致
- [ ] React Query hooks 的 queryKey 唯一且结构合理
- [ ] mutation hooks 包含缓存失效逻辑
- [ ] import 路径正确，无循环依赖
- [ ] 代码风格符合项目 ESLint/Prettier 配置
- [ ] TypeScript 编译通过（`tsc --noEmit`）
- [ ] index.ts 导出完整，无遗漏
- [ ] 文件上传/下载端点使用正确的 Content-Type 处理
- [ ] 错误类型 `ApiClientError` 包含完整信息（status, body, url, method）

---

## 决策流程图

```
获取 OpenAPI Spec（URL / 文件 / 粘贴）
        |
验证 spec 格式是否有效？
  否 -> 报告错误并停止
  是 |
        |
解析 spec：paths、schemas、securitySchemes
        |
读取项目配置：tsconfig / eslint / prettier / package.json
        |
检测项目已有依赖：axios? react-query? swr?
        |
生成 TypeScript 类型定义（types.ts）
        |
选择 HTTP 客户端类型
  项目有 axios -> axios client
  其他 -> fetch client（零依赖）
        |
生成 client.ts（含认证、重试、拦截器）
        |
按 tag 分组生成 API 函数（api/*.ts）
        |
是否需要 React Query hooks？
  项目有 @tanstack/react-query 或用户要求 -> 生成 hooks/*.ts
  否 -> 跳过
        |
是否需要 SWR hooks？
  项目有 swr 或用户要求 -> 生成 hooks/*.swr.ts
  否 -> 跳过
        |
生成 index.ts（统一导出入口）
        |
运行 tsc 类型检查 + eslint + prettier
  失败 -> 修复后重新验证
  通过 |
        |
输出结果 + 质量检查报告
```

---

## 注意事项

- **不要**生成 `any` 类型，遇到无法推断的类型使用 `unknown`
- **不要**硬编码 baseUrl，必须通过 config 传入
- **不要**在生成的代码中包含 console.log
- **不要**忽略 spec 中的 `required` 字段定义
- **不要**遗漏错误响应类型（400、401、403、404、500）
- 大型 spec（100+ 端点）按 tag 拆分文件，避免单文件过大
- 生成后建议用户检查认证配置是否与实际 token 获取方式匹配
- 若 spec 版本为 Swagger 2.0，先提示用户升级或自动转换为 OpenAPI 3.0
- 对 `allOf` 继承关系，使用 TypeScript `extends` 而非交叉类型（当适用时）
