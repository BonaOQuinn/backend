This is a small python implementation of a distributed caching system using consistent-hashing. Servers can only handle so many requests at a time,
and when data is stored in one central location thousands if not million of hits at a time can greatly reduce app speed. Caching provides a solution, 
by storing copies of data in other locations, it can reduce latency and keep servers from shutting down. However, data is constantly being updated, and 
what if users need to access time-sensitive information such as bank statements, or want to open up their most recent shopping cart into a new window? That 
means we need to continuously update servers, and taking the time to update any number of cache server is very costly. A distributed caching system helps solve 
that by keeping up to date data in multiple servers at any given time, this also creates a failsafe in case a certain server with certain information shuts down. 
A distributed caching system uses nodes to hold the location of cache server, and each server has a dedicated number of nodes to represent it, and in the case of
consistent hashing, each node is hashed onto a "ring structure", and the same hash function is used when fetching or pulling data. The cycle goes something like this:
- a request is sent from the client side
- the cache API provides a way for the request to the cache system
- the request is then hashed and a binary search is used to travel the ring and find the successor of where the hash would land on the ring
- that node then send the request to the cache server it represents
- a second hash function is used to map the key of the request to the data it wants to access from the cache server
- the server then returns the data to client
