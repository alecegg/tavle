# Serve

## Orientation

The loopback HTTP server for one Markdown page. `serve` runs the server, `server_parts` holds its reusable checks, headers, live updates and assets, `assemble_served` builds served pages and their comment threads, and `netbind` decides which host values are loopback and which hosts and origins the server accepts.
