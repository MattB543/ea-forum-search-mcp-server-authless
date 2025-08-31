# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Cloudflare Workers-based MCP (Model Context Protocol) server that runs without authentication. It provides EA Forum search capabilities using vector embeddings and semantic similarity. The server connects to a PostgreSQL database with pgvector extension and uses OpenAI embeddings for search functionality.

## Development Commands

- `npm run dev` or `npm start`: Start local development server with Wrangler
- `npm run deploy`: Deploy to Cloudflare Workers
- `npm run format`: Format code using Biome
- `npm run lint:fix`: Run Biome linter and auto-fix issues
- `npm run type-check`: Run TypeScript type checking without emitting files
- `npm run cf-typegen`: Generate Cloudflare Workers type definitions

## Architecture

### Core Structure
- **Main entry point**: `src/index.ts` - Contains the `MyMCP` class extending `McpAgent`
- **MCP Server**: Uses `@modelcontextprotocol/sdk/server/mcp.js` for MCP protocol implementation
- **Durable Objects**: The `MyMCP` class is configured as a Cloudflare Durable Object
- **Endpoints**: 
  - `/sse` and `/sse/message`: Server-Sent Events endpoint for real-time communication
  - `/mcp`: Standard MCP endpoint

### Tool Definition Pattern
Tools are defined in the `init()` method of the `MyMCP` class using:
```typescript
this.server.tool(name, schema, handler)
```
Where:
- `name`: Tool identifier
- `schema`: Zod schema for input validation
- `handler`: Async function returning `{ content: [{ type: "text", text: string }] }`

### Current Tools
- `search_ea_posts`: Search EA Forum posts by title similarity using vector embeddings
  - Parameters: `query` (string), `limit` (number, default 10), `threshold` (number, default 0.7)
- `search_ea_comments`: Search EA Forum comments by content similarity using vector embeddings  
  - Parameters: `query` (string), `limit` (number, default 10), `threshold` (number, default 0.7)

### Environment Variables Required
- `AI_SAFETY_FEED_DB_URL`: PostgreSQL connection string with pgvector extension
- `OPENAI_KEY`: OpenAI API key for text-embedding-3-small model

### Database Schema
- **Posts table**: `fellowship_mvp` with columns: id, post_id, title, page_url, author_display_name, posted_at, title_embedding_gemini (1536-dim vector)
- **Comments table**: `fellowship_mvp_comments` with columns: id, comment_id, post_id, markdown_content, author_display_name, posted_at, content_embedding (1536-dim vector)

## Code Style

- Uses Biome for formatting and linting
- Indent width: 4 spaces
- Line width: 100 characters
- Strict TypeScript enabled
- Target: ES2021 with bundler module resolution

## Deployment

Runs on Cloudflare Workers with:
- Node.js compatibility enabled
- Durable Objects for stateful operations
- SSE support for real-time MCP communication
- Observability enabled