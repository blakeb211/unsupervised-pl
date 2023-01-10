# Wrapper class over database or cache so that it can easily be switched out

# Uses
1. underlying storage can be a shelve file, a mongo database, a postgres database, etc
1. write application code once and only modify the wrapper if the backing storage changes
1. database dependency isolated to the wrapper

# Input
1. entry name (programming language name in current example)
1. returns (tuple of text, date)

# Functions
1. open_or_create - open database or create new one
1. find - returns an entry or None
1. keys - returns a list of the keys
1. insert_or_update - adds a new entry or updates existing entry
1. delete - delete a record
