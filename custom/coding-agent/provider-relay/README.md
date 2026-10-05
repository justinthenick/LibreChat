# Coding-agent provider relay

This container is the narrow provider boundary used by contained ACP sessions.

The ACP sandbox does not receive ChatGPT/OpenAI provider credentials and does
not receive public network access. It receives only a short-lived,
Broker-signed, task-bound relay token and can reach only the reviewed relay on
the isolated ACP provider network.

The relay:

- validates the Broker HMAC token before serving provider requests;
- validates audience, task, model, issue time, expiry and nonce;
- rejects non-canonical Base64URL token encodings before signature acceptance;
- accepts only the fixed reviewed model;
- bounds request and response sizes;
- forwards only prompt text to the private Codex adapter Unix socket;
- never receives Codex/ChatGPT OAuth credentials;
- never returns raw Codex stderr or authentication material;
- maps backend failures to bounded provider errors.

The Codex adapter remains host-side because ChatGPT authentication is owned by
the trusted operator account. Its model-visible tools are hard-disabled in
code. Unexpected Codex tool events fail closed.

The relay container is intended to run non-root with a read-only root
filesystem, all Linux capabilities dropped, no-new-privileges, bounded
resources, one isolated ACP network attachment and exactly one reviewed,
read-only bind of the adapter socket directory.

Callers do not select relay image, command, network, socket, model or mounts.

Contained ACP sessions use provider ID `coding-agent-relay` and the fixed
model alias `coding-agent-text`. This alias identifies the bounded text backend;
it does not allow callers to select an upstream model. Deploy the sandbox
configuration, relay image and relay runtime policy together when changing it.
