# This is a little Tool to compare the responses of different (local) LLMs that run under Ollama with each other 
# simply fill out the parameters section and run it
# use as is, no License, no liability, no Support!

from langchain_ollama import OllamaLLM
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import os
from datetime import datetime


# setting parameters
model = "" # leave that empty!

# List of Models that are available on your Ollama Instance
avail_models = ["llama3.2","nemotron-mini","hermes3","llama3:8b"]

# desired Temperature for the test
temp = 0.7

# Url where the Ollama API is available
oll_url = "http://localhost:11434"

# The Question/Promt tht the LLM is supposed to answer
frage = "why is the sky blue?"

#############

# Create output directory if it doesn't exist
output_dir = "model_outputs"
os.makedirs(output_dir, exist_ok=True)
    
# Current timestamp for the output files
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")



def setup_ollama_model(model_name=model, temperature=temp, base_url=oll_url):
    """
    Sets up an Ollama model with specified parameters.
    
    Args:
        model_name (str): Name of the Ollama model to use
        temperature (float): Temperature parameter for response generation
        base_url (str): Base URL for the Ollama instance
    
    Returns:
        OllamaLLM: Configured Ollama model instance
    """
    # Create callback manager for streaming output
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
    
    # Initialize Ollama with specified parameters
    llm = OllamaLLM(
        model=model_name,
        callbacks=[StreamingStdOutCallbackHandler()],  # Using callbacks instead of callback_manager
        temperature=temperature,
        base_url=base_url,
        # Additional parameters you might want to adjust:
        # num_ctx=4096,         # Context window size
        # top_k=10,            # Number of tokens to consider for sampling
        # top_p=0.9,           # Nucleus sampling parameter
        # repeat_penalty=1.1    # Penalty for repeating tokens
    )
    
    return llm

def send_query(llm, query):
    """
    Sends a query to the model and returns the response.
    
    Args:
        llm: Configured Ollama model instance
        query (str): Query to send to the model
    
    Returns:
        str: Model's response
    """
    try:
        response = llm.invoke(query)
        return response
    except Exception as e:
        print(f"Error occurred while querying the model: {e}")
        return None

def main():
    
    query = frage
    # Create filename
    filename = f"{output_dir}/{query[:30].replace(' ', '_')}@{temp}.md"
                
    for model in avail_models:
        # for temp in temperatures:
        try:   
            # Initialize model
            llm = setup_ollama_model(model_name=model,temperature=temp)

            print("\nSending query to Ollama...")
            print(f"Query: {query}\nAnswer from {model}@{temp}:\n")
            
            # Send query and get response
            response = send_query(llm, query)

            if response:
                print("\n####################### Query completed successfully!\n")
                
                # Write to markdown file
                with open(filename, 'a', encoding='utf-8') as f:
                    f.write(f"# Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"## Prompt:\n")
                    f.write(f"{query}\n\n")
                    f.write(f"## Answer from **{model}@{temp}**\n")
                    f.write(f"{response}\n")
                
                print(f"Output saved to: {filename}")

                
        except Exception as e:
            print(f"Error processing model {model}: {str(e)}")
            continue

if __name__ == "__main__":
    main()
