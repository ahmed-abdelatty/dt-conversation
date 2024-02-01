import utils
import streamlit as st
from streaming import StreamHandler


from dotenv import load_dotenv
from typing import TypedDict, Annotated, Sequence
import operator

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt.tool_executor import ToolExecutor
from langchain.tools.render import format_tool_to_openai_function
from langgraph.prebuilt import ToolInvocation
import json
from langchain_core.messages import FunctionMessage
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()
st.set_page_config(page_title="Digital Twin", page_icon="📄", layout="wide")
initial_state = {
    "template": """you are max a helpful assistant, you need to maintain converstion with the user,
    also you should be aware of the home states, initially the ac, tv and the lights are on.
    In addition, you mange user schedual.
    You also should provide a recommendation for the user, if the user ask for one or shared his/her feeling.""",
    "temperature": 0.0,
    "model": "gpt-4-1106-preview"
}

for key, value in initial_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


class GraphChatExecutor:

    def __init__(self, model, temperature, prompt):
        utils.configure_openai_api_key()

        self.model = ChatOpenAI(model=model, temperature=temperature, streaming=True)
        
        self.tools = utils.define_custom_tools()
        self.tool_executor = ToolExecutor(self.tools)

        functions = [format_tool_to_openai_function(t) for t in self.tools]
        self.model = self.model.bind_functions(functions)
        
        self.graph = self.setup_graph()

        self.messages = {"messages": [SystemMessage(content=prompt)]}
        
    # Define the function that determines whether to continue or not
    def should_continue(self, state):
        messages = state['messages']
        last_message = messages[-1]
        # If there is no function call, then we finish
        if "function_call" not in last_message.additional_kwargs:
            return "end"
        # Otherwise if there is, we continue
        else:
            return "continue"

    # Define the function that calls the model
    def call_model(self, state):
        messages = state['messages']
        response = self.model.invoke(messages)
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}

    # Define the function to execute tools
    def call_tool(self, state):
        messages = state['messages']
        # Based on the continue condition
        # we know the last message involves a function call
        last_message = messages[-1]
        # We construct an ToolInvocation from the function_call
        action = ToolInvocation(
            tool=last_message.additional_kwargs["function_call"]["name"],
            tool_input=json.loads(last_message.additional_kwargs["function_call"]["arguments"]),
        )
        print(f"The agent action is {action}")
        # We call the tool_executor and get back a response
        response = self.tool_executor.invoke(action)
        print(f"The tool result is: {response}")
        # We use the response to create a FunctionMessage
        function_message = FunctionMessage(content=str(response), name=action.tool)
        # We return a list, because this will get added to the existing list
        return {"messages": [function_message]}
    
    def setup_graph(self):
        # Define a new graph
        workflow = StateGraph(AgentState)
        
        # Define the two nodes we will cycle between
        workflow.add_node("agent", self.call_model)
        workflow.add_node("action", self.call_tool)
        
        # Set the entrypoint as `agent` where we start
        workflow.set_entry_point("agent")
        
        # We now add a conditional edge
        workflow.add_conditional_edges(
            # First, we define the start node. We use `agent`.
            # This means these are the edges taken after the `agent` node is called.
            "agent",
            # Next, we pass in the function that will determine which node is called next.
            self.should_continue,
            # Finally we pass in a mapping.
            # The keys are strings, and the values are other nodes.
            # END is a special node marking that the graph should finish.
            # What will happen is we will call `should_continue`, and then the output of that
            # will be matched against the keys in this mapping.
            # Based on which one it matches, that node will then be called.
            {
                # If `tools`, then we call the tool node.
                "continue": "action",
                # Otherwise we finish.
                "end": END
            }
        )
        
        # We now add a normal edge from `tools` to `agent`.
        # This means that after `tools` is called, `agent` node is called next.
        workflow.add_edge('action', 'agent')
        
        # Finally, we compile it!
        # This compiles it into a LangChain Runnable,
        # meaning you can use it as you would any other runnable
        return workflow.compile()
    
    @st.spinner('Running the model..')
    def run(self, message):
        self.messages["messages"].append(HumanMessage(content=message))
        self.messages = self.graph.invoke(self.messages)
        return self.messages['messages'][-1].content


    
@utils.enable_chat_history
def main():   
    if 'graph_model' not in st.session_state:
        st.session_state.graph_model = GraphChatExecutor(
            model=initial_state["model"],
            prompt=initial_state['template'],
            temperature=initial_state['temperature']
        ) 
        
    with st.sidebar:
        st.header('Chat with DT')
        prompt_template = st.text_area(label="Enter the prompt: ", value=st.session_state.template, height=250)
        prompt_template = prompt_template.strip()
        # if not prompt_template:
        #     st.error("You must enter a prompt", icon="🚨")
        #     st.stop()
        # else:
        #     selectbox_change(1)
        
        model = st.selectbox("Choose a model: ", ['gpt-3.5-turbo', 'gpt-4'], index=1).strip()
        temperature = st.slider('Choose the temperature value: ', 0.0, 1.0, st.session_state.temperature)
        
        st.session_state.template = prompt_template
        st.session_state.model = model
        st.session_state.temperature = temperature
        
    user_query = st.chat_input(placeholder="Ask me anything!")
    if user_query:
        utils.display_msg(user_query, 'user')
        with st.chat_message("assistant"):
            #st_cb = StreamHandler(st.empty())
            response = st.session_state.graph_model.run(user_query)
            st.empty().markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()