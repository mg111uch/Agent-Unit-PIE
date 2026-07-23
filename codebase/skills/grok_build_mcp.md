You can connect Grok Build to a local Model Context Protocol (MCP) server either via the CLI command or by updating your local configuration file.  

Because Grok Build runs locally on your machine, it natively supports local  communication and does not require external network tunneling for local subprocesses. 

## Method 1: Use the CLI Command (Fastest) 
The absolute fastest way to hook up your local server is using the  command from your terminal. Everything you append after the double-dash (--) represents the exact command used to spawn your local server: [1] 

```bash
grok mcp add <server-name> -- <command> [args...]
```
Examples: 

• Python-based server:  
```bash
grok mcp add my-python-server -- python3 /path/to/server.py
```

## Method 2: Modify  (Persistent) 
If you want to manage your servers manually or add environment variables, you can declare them inside your global or project-level configuration file. 

1. Open your configuration file in a text editor: 

	• Global Scope: `~/.grok/config.toml` 
	• Project Scope: Create or edit `.grok/config.toml` inside your specific repository.  

2. Append your local `stdio` server details using this structure: 

```toml
[mcp_servers.my_local_server]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/secure/folder"]
env = { API_KEY = "${MY_API_KEY}" }
startup_timeout_sec = 30
tool_timeout_sec = 60
```

## Method 3: Connect via the TUI (In-Session) 
If you are already inside an active Grok Build interactive session: 

1. Type `/mcp` inside the terminal window to open the extensions modal. 
2. Navigate to the MCP tab. 
3. Click Add New Server and input your local configuration details directly into the user interface.  

## Verify the Connection 
Once you have added the server using any of the options above, verify that Grok can communicate with it: 

• Run `grok mcp list` to check if your server appears in the active integrations list. 
• Run `grok mcp doctor <server-name>` to diagnose any connectivity bugs, path formatting issues, or tool timeout failures. 
• Execute `grok inspect` inside your project directory to see all active tools discovered by the runtime. [1, 9, 10]  

[1] https://docs.x.ai/build/features/mcp-servers
[2] https://docs.x.ai/grok/connectors/custom-mcp-tunneling
[3] https://docs.x.ai/build/settings


