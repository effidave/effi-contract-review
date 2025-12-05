### IDEAS
AGENTS.md to explain the skills
- UK qualified lawyer etc.
- here are the tools
- here is how precedents work [including drafting notes]
- if acting for customer
- if acting for supplier

template project dir with the structure needed

ability to create a new project through the app

Q&A chat to understand and create 
- a context file for the client
- a context file for the instruction

Q&A chat to identify an appropriate precedent
- for now user will manually put this into the right place
- in the future the app will access a precedent bank
- and provide an opportunity for user to upload new precedent
- and provide a context file for each precedent

auto-git the artifacts 'with a useful message'
update the artifacts on each change - but how to preserve the uuids?
create an md file based on the blocks on each change - and use this as the context alongside all other contexts

generate paraId for new blocks:
Random rnd = new();
int idNum = rnd.Next(1, int.MaxValue);
string newId = idNum.ToString("X8");
[but also check for collisions with existing paraIds]

make sure track changes is rendering deleted text