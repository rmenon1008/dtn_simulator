Contains peripherals which can be used to handle all roaming client-related content.

The data-exchange process between the client and router payload handlers should roughly be as follows:

1. client asks router if there are any payloads waiting for the client.

2. router returns list of IDs of all payloads it has on-hand for the client

3. client looks at list, figures out which payloads it needs.  client then asks router for payloads it doesn't have.

4. router sends desired payloads to client.

5. client receives desired payloads, uploads to the router any payloads it needs to send.

6. router stores payloads sent by client.

Doing this process minimizes network usage to ensure that we only send full bundles on an as-needed basis.  
Since payloads can be on GB-to-TB scale, this metadata-based check is important.