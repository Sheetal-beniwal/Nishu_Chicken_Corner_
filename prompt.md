I am building a restaurant order management ai system using langgraph.

I will explain you very clearly what i want and what is architecture i will also explain you stats nodes and edges in the end i will give u tescases to simulate so you tell me whether they pass or not.

The rough plan is:

There will be a user. when the code runs the user will give a order this will be taken as input which i will type.
This order shpu;ld go to the LLM. the order as of noe should contain the name of dish and required quantity for now we will limit the order to 1 dish and whatever quantity.
The llm has to extract the order dish name and quantity.
if the  user irder is not related to food ordering the llm should not entertain it and it should return the user that this request is not related to food ordering query .

once the llm has order dish and quantity it wills end this to a node called order_confirm.

the task of this order confirm is to look at the menu that i will share with you then this node will decide one of 3 cases.
the order is available.
the order is partially available means quantuty available is not sufficent.
the order is not available at all means either the dish that ser asked is not in menu ot that dish availabilbility is 0.

it will put this in the status of the state(i will tell you exact content of langgrapg state as well)

once the llm recieve this
if the status is confiremed it should call another node called cook
if status is partial nor not availabe it should again prompt the user tp decide if he wants to give another order or go ahed with partial order.

this order retries will be limited to 3 times means if afte 3 tries the user order is not satisfied system will come to end mode


Now when the cook node is called there can be 2 cases.
either the cook is done then status will be ready if cook is fails (we can use probability function give 40% chances of fail and 60% chance of success)
if cook is fals then there should be retry limit of 2 if it fails even after 2 retry then it will send apology to user and system will will come to end

if cook succeds, the status will be ready and the next node will be called which is serve

similar to cook it also has 2 cases serve pass or serve fail
this also has 2 retry attempts if serve fails after 2 attemps it will send apology to the user and system end
if success than the status will be complete the llm should prompt the user saying your order is ready 

if serve fails the cook should be called one more time to retry note that if cook has exhausted its retry attemps then it should not cook again and it should give apology to user ans come to end state

now the state of langgraphg

there should be a annotated message betweem llm and user
there should be order details 
dish name as string
required quantity as string
available quantity as string

order_confirm will write available quanity by reading the menu
the llm should get to know the order confirm status by reading the state

if a dish is not available in the menu order confirm should write 0 as available quanity 

then there should be status each node will update their status as defined in above rules

there should be retry attempst 
order retry 3
cook retry 2
serve retry 2

each time failure happend it should decrement the attemps if any retry counter is 0 llm should understand whether t has to give retry or issue appology to user reading the counters

in the end there should be final result where order is complete or not if not then with reason.

write the code and ask if tere are any poen questions from your side then ask i will give you some test scenerios to test later on

i have given groq api key in my .env file and menu in pdf form [निशु चिकन कॉर्नर.pdf](<C:\Users\SHEETAL\Desktop\coding\aiCourse\restaurantagent\निशु चिकन कॉर्नर.pdf>) with dish name and price by default take availabe quantity as 3.
    