"""Source adapters. In production each is a different system; here each reads the file that stands in
for that system. Each adapter returns raw records AND how long it took, so the replay can show the fetch."""
