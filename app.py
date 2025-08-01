from flask import Flask, request, jsonify, session
from flask_cors import CORS
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch  # <-- IMPORTANT: This library is now required for tensor operations

app = Flask(__name__)
CORS(app)
# !!! IMPORTANT: A secret key is required for Flask sessions !!!
# In a real application, make this a long, random, and securely stored string.
app.secret_key = 'your_super_secret_chatbot_key_12345'  # Please change this value!

# --- Model Loading ---
MODEL_NAME = "microsoft/DialoGPT-small"  # Still using the smaller model for faster loading

tokenizer = None
model = None

try:
    print(f"Loading Hugging Face model and tokenizer for: {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

    # For DialoGPT, it's common to set the padding token to the EOS token for generation.
    # This ensures the model knows where a response should end.
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    if hasattr(model.config, 'pad_token_id'):
        model.config.pad_token_id = model.config.eos_token_id
    else:
        # Add the attribute if it doesn't exist, as some models might not have it by default
        model.config.add_attribute("pad_token_id", model.config.eos_token_id)

    print(f"{MODEL_NAME} loaded successfully! (Running on CPU)")

except Exception as e:
    print(f"Error loading Hugging Face model {MODEL_NAME}: {e}")
    print("Possible reasons: Network issue, typo in model name, or firewall blocking access.")
    tokenizer = None
    model = None


# --- Chat Endpoint ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({'response': 'No message provided.'}), 400

    if tokenizer and model:
        try:
            # Retrieve conversation history (list of token IDs) from Flask session
            # If no history exists (first message), initialize as None
            chat_history_ids = session.get('chat_history_ids', None)

            # If history exists, convert the list back into a PyTorch tensor
            if chat_history_ids is not None:
                chat_history_ids = torch.tensor(chat_history_ids)

            # Encode the new user message. Add the EOS token to mark the end of the user's turn.
            new_input_ids = tokenizer.encode(user_message + tokenizer.eos_token, return_tensors='pt')

            # Concatenate the new user input with the existing chat history
            # If no history, the bot's input is just the new message
            bot_input_ids = new_input_ids if chat_history_ids is None else \
                torch.cat([chat_history_ids, new_input_ids], dim=-1)

            # Determine the maximum length for the generation, considering current history and new tokens.
            # We add 60 for the new tokens, and ensure it doesn't exceed the model's max capacity (e.g., 1024 for DialoGPT-small).
            max_length_current = bot_input_ids.shape[-1] + 60
            if max_length_current > model.config.max_position_embeddings:
                # If history is too long, truncate it to fit within the model's context window.
                # We keep the most recent part of the conversation.
                bot_input_ids = bot_input_ids[:, -model.config.max_position_embeddings + 60:]

            # Generate a response from the model
            # The model will use the entire 'bot_input_ids' as context
            chat_history_ids = model.generate(
                bot_input_ids,
                max_new_tokens=60,  # Max tokens for the AI's current response
                num_return_sequences=1,  # Generate only one response
                pad_token_id=tokenizer.eos_token_id,  # Use EOS token for padding
                no_repeat_ngram_size=3,  # Prevent simple repetition of 3-word sequences
                do_sample=True,  # Enable sampling for more diverse responses
                top_k=50,  # Sample from top 50 likely tokens
                temperature=0.7  # Controls randomness: lower = more predictable, higher = more creative
            )

            # Decode only the NEW part of the response generated by the AI
            # We skip the input history part that was sent to the model.
            response_text = tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)

            # Store the entire updated conversation history (including AI's new response) back into the session
            # Convert the PyTorch tensor to a Python list for Flask session serialization
            session['chat_history_ids'] = chat_history_ids.tolist()

            # Basic post-processing for cleaner output (e.g., removing extra spaces, adding punctuation)
            if not response_text or response_text.isspace() or len(response_text.split()) < 2:
                response_text = "I'm not sure how to respond to that."
            elif not response_text.endswith(('.', '?', '!')):
                response_text += '.'

            return jsonify({'response': response_text})

        except Exception as e:
            print(f"Error during text generation: {e}")
            return jsonify({'response': "I'm having trouble generating a response right now. Please try again."}), 500
    else:
        # Fallback if model failed to load during startup
        return jsonify({'response': "AI service is not available. The model could not be loaded."}), 503


if __name__ == '__main__':
    app.run(port=5001, debug=True)