import { McpAgent } from "agents/mcp";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import OpenAI from "openai";
import postgres from "postgres";

// Types for EA Forum data
interface PostResult {
    id: number;
    post_id: string;
    title: string;
    url?: string;
    author?: string;
    posted_at?: Date;
    similarity_score: number;
}

interface CommentResult {
    id: number;
    comment_id: string;
    post_id: string;
    content?: string;
    author?: string;
    posted_at?: Date;
    similarity_score: number;
}

// Define our MCP agent with EA Forum search tools
export class MyMCP extends McpAgent {
	server = new McpServer({
		name: "EA Forum Search",
		version: "1.0.0",
	});

    private openaiClient?: OpenAI;
    private dbConnection?: ReturnType<typeof postgres>;
    // Initialize database and OpenAI connections
    private async initConnections() {
        // Access environment variables
        const dbUrl = process.env.AI_SAFETY_FEED_DB_URL;
        const openaiKey = process.env.OPENAI_KEY;

        if (!this.openaiClient && openaiKey) {
            this.openaiClient = new OpenAI({
                apiKey: openaiKey,
            });
        }

        if (!this.dbConnection && dbUrl) {
            // Convert postgresql:// to proper connection string if needed
            let connectionUrl = dbUrl;
            if (connectionUrl.startsWith("postgresql://")) {
                connectionUrl = connectionUrl.replace("postgresql://", "postgres://");
            }
            this.dbConnection = postgres(connectionUrl);
        }
    }

    // Get embedding for a query using OpenAI
    private async getQueryEmbedding(query: string): Promise<number[]> {
        if (!this.openaiClient) {
            throw new Error("OpenAI client not initialized");
        }

        const response = await this.openaiClient.embeddings.create({
            model: "text-embedding-3-small",
            input: query,
        });

        return response.data[0].embedding;
    }

    // Search EA Forum posts by title similarity
    private async searchSimilarPosts(
        query: string,
        limit: number = 10,
        threshold: number = 0.7
    ): Promise<PostResult[]> {
        if (!this.dbConnection) {
            throw new Error("Database connection not initialized");
        }

        const embedding = await this.getQueryEmbedding(query);
        const embeddingStr = `[${embedding.join(",")}]`;

        const rows = await this.dbConnection`
            SELECT 
                id, post_id, title, page_url, author_display_name, posted_at,
                1 - (title_embedding_gemini <=> ${embeddingStr}) as similarity_score
            FROM fellowship_mvp 
            WHERE title_embedding_gemini IS NOT NULL
                AND 1 - (title_embedding_gemini <=> ${embeddingStr}) >= ${threshold}
            ORDER BY similarity_score DESC
            LIMIT ${limit}
        `;
        
        return rows.map(row => ({
            id: row.id,
            post_id: row.post_id,
            title: row.title,
            url: row.page_url,
            author: row.author_display_name,
            posted_at: row.posted_at,
            similarity_score: Math.round(parseFloat(row.similarity_score) * 1000000) / 1000000
        })).filter(result => 
            !Number.isNaN(result.similarity_score) && 
            result.similarity_score >= threshold &&
            result.similarity_score <= 1
        );
    }

    // Search EA Forum comments by content similarity
    private async searchSimilarComments(
        query: string,
        limit: number = 10,
        threshold: number = 0.7
    ): Promise<CommentResult[]> {
        if (!this.dbConnection) {
            throw new Error("Database connection not initialized");
        }

        const embedding = await this.getQueryEmbedding(query);
        const embeddingStr = `[${embedding.join(",")}]`;

        const rows = await this.dbConnection`
            SELECT 
                id, comment_id, post_id, markdown_content, author_display_name, posted_at,
                1 - (content_embedding <=> ${embeddingStr}) as similarity_score
            FROM fellowship_mvp_comments 
            WHERE content_embedding IS NOT NULL
                AND 1 - (content_embedding <=> ${embeddingStr}) >= ${threshold}
            ORDER BY similarity_score DESC
            LIMIT ${limit}
        `;
        
        return rows.map(row => ({
            id: row.id,
            comment_id: row.comment_id,
            post_id: row.post_id,
            content: row.markdown_content,
            author: row.author_display_name,
            posted_at: row.posted_at,
            similarity_score: Math.round(parseFloat(row.similarity_score) * 1000000) / 1000000
        })).filter(result => 
            !Number.isNaN(result.similarity_score) && 
            result.similarity_score >= threshold &&
            result.similarity_score <= 1
        );
    }

	async init() {
        // EA Forum post search tool
        this.server.tool(
            "search_ea_posts",
            {
                query: z.string().describe("Search query for EA Forum posts"),
                limit: z.number().optional().default(10).describe("Maximum number of results to return"),
                threshold: z.number().optional().default(0.7).describe("Similarity threshold (0-1)")
            },
            async ({ query, limit, threshold }) => {
                try {
                    await this.initConnections();
                    const results = await this.searchSimilarPosts(query, limit, threshold);
                    
                    if (results.length === 0) {
                        return {
                            content: [{
                                type: "text",
                                text: `No EA Forum posts found matching "${query}" with similarity >= ${threshold}`
                            }]
                        };
                    }

                    const resultText = results.map(post => 
                        `**${post.title}** (Score: ${post.similarity_score})\n` +
                        `Author: ${post.author || 'Unknown'}\n` +
                        `URL: ${post.url || 'N/A'}\n` +
                        `Posted: ${post.posted_at ? new Date(post.posted_at).toLocaleDateString() : 'Unknown'}\n`
                    ).join('\n---\n\n');

                    return {
                        content: [{
                            type: "text",
                            text: `Found ${results.length} EA Forum posts matching "${query}":\n\n${resultText}`
                        }]
                    };
                } catch (error) {
                    return {
                        content: [{
                            type: "text",
                            text: `Error searching EA Forum posts: ${error instanceof Error ? error.message : String(error)}`
                        }]
                    };
                }
            }
        );

        // EA Forum comment search tool  
        this.server.tool(
            "search_ea_comments",
            {
                query: z.string().describe("Search query for EA Forum comments"),
                limit: z.number().optional().default(10).describe("Maximum number of results to return"),
                threshold: z.number().optional().default(0.7).describe("Similarity threshold (0-1)")
            },
            async ({ query, limit, threshold }) => {
                try {
                    await this.initConnections();
                    const results = await this.searchSimilarComments(query, limit, threshold);
                    
                    if (results.length === 0) {
                        return {
                            content: [{
                                type: "text", 
                                text: `No EA Forum comments found matching "${query}" with similarity >= ${threshold}`
                            }]
                        };
                    }

                    const resultText = results.map(comment => 
                        `**Comment by ${comment.author || 'Unknown'}** (Score: ${comment.similarity_score})\n` +
                        `Post ID: ${comment.post_id}\n` +
                        `Posted: ${comment.posted_at ? new Date(comment.posted_at).toLocaleDateString() : 'Unknown'}\n` +
                        `Content: ${comment.content ? comment.content.substring(0, 200) + (comment.content.length > 200 ? '...' : '') : 'N/A'}\n`
                    ).join('\n---\n\n');

                    return {
                        content: [{
                            type: "text",
                            text: `Found ${results.length} EA Forum comments matching "${query}":\n\n${resultText}`
                        }]
                    };
                } catch (error) {
                    return {
                        content: [{
                            type: "text",
                            text: `Error searching EA Forum comments: ${error instanceof Error ? error.message : String(error)}`
                        }]
                    };
                }
            }
        );
	}
}

export default {
	fetch(request: Request, env: Env, ctx: ExecutionContext) {
		const url = new URL(request.url);

		if (url.pathname === "/sse" || url.pathname === "/sse/message") {
			return MyMCP.serveSSE("/sse").fetch(request, env, ctx);
		}

		if (url.pathname === "/mcp") {
			return MyMCP.serve("/mcp").fetch(request, env, ctx);
		}

		return new Response("Not found", { status: 404 });
	},
};
