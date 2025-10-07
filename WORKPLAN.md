
- Rename display_full_email() to process_email()

- Start parsing from the oldest emails in order to capture the initial context where the name of the use case etc might be.

- belterra-maintenance@googlegroups.com

- Seed well NER & context
- Do NER with each email, check with user for confirmations
- It's going to be useful to go back after some initial discovery and redo the NER name entity recognition process and enriching

- save extracted email as formatted by display_full_email() in Neo4J DB as a new node. We'll create edges later. Save the email's internetMessageId as a node property in a way that allows us to create an index over it for faster search later. 

# DONE

