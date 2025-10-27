import os
import time
import json
import logging
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  handlers=[
    logging.FileHandler('chat_app.log'),
    logging.StreamHandler()
  ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configure Gemini API
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
model_name = 'gemini-flash-lite-latest'

# Pricing information for Gemini Flash (as of 2024)
PRICING_PER_TOKEN = {
  'input': 0.0001 / 1000,    # $.10 per 1M tokens
  'output': 0.0004 / 1000    # $.40 per 1M tokens
}

# Safety Settings
safety_settings = [
  types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
  types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
  types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
  types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
]

def format_conversation_for_gemini(messages):
  """Format the last 5 messages for Gemini API"""
  formatted_messages = []
  
  for msg in messages:
    role = "user" if msg["role"] == "user" else "model"
    formatted_messages.append(types.Content(
      role=role,
      parts=[types.Part.from_text(text=msg["content"])]
    ))
  
  return formatted_messages

def calculate_cost(input_tokens, output_tokens):
  """Calculate the cost based on token usage"""
  input_cost = input_tokens * PRICING_PER_TOKEN['input']
  output_cost = output_tokens * PRICING_PER_TOKEN['output']
  return input_cost + output_cost

@app.route('/chat', methods=['POST'])
def chat():
  # Generate unique request ID for tracking
  request_id = str(uuid.uuid4())[:8]
  start_time = time.time()
  
  try:
    data = request.get_json()
    messages = data.get('messages', [])
    
    # Log incoming request details
    logger.info(f"[{request_id}] Chat request received - Messages count: {len(messages)}")
    logger.info(f"[{request_id}] Request IP: {request.remote_addr}")
    logger.info(f"[{request_id}] User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    if not messages:
      logger.warning(f"[{request_id}] No messages provided in request")
      return jsonify({'error': 'No messages provided'}), 400
    
    # Log conversation summary
    conversation_summary = []
    for i, msg in enumerate(messages):
      role = msg.get('role', 'unknown')
      content_preview = msg.get('content', '')[:100] + '...' if len(msg.get('content', '')) > 100 else msg.get('content', '')
      conversation_summary.append(f"{role}: {content_preview}")
    
    logger.info(f"[{request_id}] Conversation summary: {' | '.join(conversation_summary)}")
    
    # Take only the last 5 messages
    recent_messages = messages[-5:] if len(messages) > 5 else messages
    logger.info(f"[{request_id}] Using {len(recent_messages)} recent messages (truncated from {len(messages)} total)")
    
    # Format conversation for Gemini
    formatted_messages = format_conversation_for_gemini(recent_messages)
    
    # Create system prompt for HR specialist
    system_prompt = """You are Optum's Retirement Specialist, an AI assistant designed to help employees with retirement questions and concerns. You should:
1. Provide accurate, concise, and helpful information about retirement policies, benefits, and procedures.  **Focus on the Philippine market.**
2. Be professional, empathetic, and supportive.  Do not expand the explanation beyond 100 words.  Wait for the user to ask for more information.
3. Guide employees to the right resources when needed
4. Use the information in the KNOWLEDGE_BASE to answer questions.

<KNOWLEDGE_BASE>

## Optum Retirement FAQ

### How often can I use the Individual Retirement Account online service?

You can use and access your Individual Retirement Account anytime at your convenience. Contributions will be posted twice a month (15th and 30th) within twenty business days from deduction, and Gain/(Loss) shall be posted once a month.

### Will I receive paper statements?

Employees will no longer receive paper statements. All information can already be viewed anytime through the portal.

### How can I confirm that a contribution was made?

View the Account Activity tab to see the Contribution transactions pertaining to your account.

### How can I confirm that an Accumulated Gain/Loss from the Fund was posted to my account?

View the Account Activity tab to see the Gain/Loss transactions pertaining to your account.

### What if there is a discrepancy in the contributions or I have other questions?

If there are any questions on the posted amounts, you can coordinate directly with the Employee Center.

### Can I change my information in the Retirement Fund Account online?

Employees can only input their contact numbers and addresses. To change any other information, kindly raise a ticket through Employee Center.

### For former employees, when will I receive my retirement benefit?

TAT is 60 business days from last working day (LWD). If beyond 60 business days, former employees may follow up their retirement benefit status via Employee Center.

### Retirement Withdrawal – when will I receive it / follow-up? How much will I get?

You will get 100% of your Employee Voluntary Contributions including earnings and losses, while the corresponding Employer Matching contributions will be forfeited as per the retirement policy. TAT is 60 business days from the final withdrawal date.

### Opted for Employee Voluntary Contributions but can’t see it on my payslip.

If you enroll between 1st – 31st of the month, the employee voluntary contributions will be deducted on the 15th payroll of the following month and the same will be reflected onyour payslip. If you nominated 5%, 7.5% or 10% of your employee voluntary contributions but didn’t see on your payslip, please reach out to Employee Center.

### How to enroll / renew?

Log in to the retirement portal (*ogs.zalamea.ph*), go to the “Enrollment” tab so you can nominate 5%, 7.5%, or 10% of your monthly basic salary. The same process is being followed for the renewal which happens every March of the year. We also have the detailed User Guide uploaded on the portal under “Resources” tab.

### Understanding vested balance, account activity, why is there a negative amount on Zalamea website?

Contributions are being invested. An investment can have gains and potential losses.

### Less than 5 years tenure would like to know if employee would get 100% of his/her retirement benefit if EE choose to resign.

An employee who resigns with less than 5 years of tenure will only be eligible to his/her employee voluntary contributions, if any. If the employee has past service contributions in his/her account, this will also be vested to the employee from 5 years of service and up in line with the vesting schedule.

### When will I be eligible for tax exemption?

Employees will be eligible for tax exemption once he reached the age of 50 and 10 years of service under the same company.

### When will I be eligible for retirement?

Employees who reached the age of 60 are eligible for Normal Retirement while for those employees who will go beyond this age, but not beyond 65 years old, will be eligible for Late Retirement, given that the employee has served the company for at least five years.

Additionally, employees with at least five years of service are eligible for Early Retirement.

### Can I separate from the company before my Early/Normal/Late Retirement Date?

Employees can separate from the company before they reach their Early / Normal / Late Retirement Date. However, employees who separate before said days are only entitled to their Employee Voluntary Balances, if any.

### Are my retirement benefit subject to the applicable Regulatory Benefit?

Yes. In cases where the employee’s Total Employer benefit is lower than the applicable Regulatory Benefit, the company shall cover the difference.

### I was hired at age 65 or older, will I be eligible for any of the company’s retirement benefit?

No. Employees hired at age 65 or older are no longer eligible for the company’s retirement plan hence retirement benefits do not apply.

Note that 65 years old is the mandatory retirement age.

### I already reached the age of 65 but has not yet reached the 5 years of service, what benefits will I be eligible to?

Employees are still entitled to retirement pay based on company guidelines, and the computation will follow the formula prescribed under the Labor Code.

### Can I cancel my voluntary withdrawal request?

Yes. Employees are given ten (10) days to retract their withdrawal request.

### When can I request another voluntary withdrawal after my previous one?

Employees can request for another withdrawal after the completion of their one-year resting period### Optum Retirement Plan Member Loan Program*### How does an employee apply for the Member Loan?

An employee who is currently participating in the Voluntary Contributions of the Retirement Fund will have to log in to the retirement portal and navigate to the Loan tab to apply for the Member Loan.

### Who are eligible to apply for the Member Loan?

Employees who are regular and are currently participating in the Voluntary Contributions of the Retirement Fund are eligible to apply for the Member Loan.

### How much can an employee borrow from the fund?

Employees can borrow up to 100% of their Voluntary Contributions \+ Earnings/Losses, provided the loan's monthly amortization does not exceed 30% of their monthly basic salary plus interest. Additionally, the loan amount must be in increments of 1,000 or divisible by 1,000. For example, if an employee's total Voluntary Contributions is PHP24,012.87, they can borrow PHP24,000. If the total Voluntary Contributions is PHP58,000.12, they can borrow PHP58,000.

### When will the borrowed amount be received and how?

The borrowed amount will be credited to the employee-borrower's Payroll account on the 15th business day after loan approval. Note that this does not follow the regular payroll crediting schedule of the 15th and 30th. BPI will credit the amount according to the bank's standard turnaround time.

  

For non-BPI accounts, an additional PHP500.00 fee will be charged by BPI on the loan proceeds.

### How will employee/borrower know if the loan is approved?

An email notification will be sent by the loan administrator to the employee-borrower’s Optum email regarding the loan status and approval.

### How can employee-borrower check the status of his / her loan application?

Loan status will be regularly shared via email by the loan administrator. Employee-borrower may check the status of the loan application by logging in to the retirement portal and navigate to the Loan tab.

### Can an employee request to expedite the loan process?

All loan applications are processed efficiently in batches, adhering to the standard turnaround time for signature routing to the Retirement Committee and the bank’s established process for crediting. This ensures a smooth and consistent experience for everyone involved.

### Will the Member Loan balance reflect on the employee’s payslip?*### the Member Loan balance will reflect on the employee-borrower’s payslip.*### Is the Member Loan interest rate fixed?

Yes, the loan interest rate is fixed and set below the market rate. It remains fixed for the entire tenure of the loan. Additionally, interest rates will be reviewed annually.

### What are the advantages of taking a loan with interest instead of withdrawing my voluntary contributions from the fund?

Applying for a loan from the retirement fund will allow you to choose the amount you wish to borrow (up to 100% of your voluntary contributions, in increments of 1,000) and your Company Matching contributions remain intact.

### Are there any documentary requirements for applying for the member loan?

Yes, there is one required document: the Promissory Note (PN). Employees need to print, read, agree to, sign, and upload this document when applying for the member loan. Important: Ensure the PN is clearly signed to avoid disapproval of your loan application. You can download the PN from the Loans tab of the retirement portal.

### What file types will the tool accept for the soft copy of the Promissory Note?

The tool accepts the following file types for the uploading of Promissory Note: 'jpeg', 'jpg', 'png', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'pdf', 'ppt', 'pptx' and up to 25MB file size only.

### How many months can employee-borrower pay for the loaned amount?

Employee-borrower can choose from the four term options to pay for the loaned amount: 6, 12, 18 and 24 months. In case where the term of the loan will exceed the employee's normal retirement age, the maximum loan term shall be adjusted accordingly. As a result, this amount will be deducted from the salary on a semi-monthly basis.

### How can employee-borrower pay for the borrowed amount?

Repayment will be set against the employee-borrowers’ salary and will be made through equal semi-monthly salary deductions.

### When will salary deductions for the payment of the loan start?

The salary deduction shall commence on the 2nd payroll date from the date of receipt by the employee-borrower of the loan and will continue with each subsequent payroll.

### Can employee-borrower pay off the loan balance in full? If yes, how?

Yes, after employee-borrower has paid at least 3 months or 6 semi-monthly installments. Full loan balance pay-off can only be requested via salary deduction by submitting an online case via Employee Center.

### Can borrower-employee stop voluntary contributions while there is an existing member loan?

While employee-borrower has an existing member loan, employee-borrower will not be able to opt out of the Voluntary Contributions.

### Can borrower-employee change the percentage of voluntary contributions while there is an existing member loan?

Yes, the employee-borrower who has an existing member loan can change the percentage of voluntary contributions to a lower or higher percentage but not zero (0).

### Can borrower-employee withdraw voluntary contributions from the fund while there is an existing member loan?

While an employee-borrower has an existing loan, voluntary contributions will remain in the fund, continuing to earn returns and receive company matching until the loan term ends. This means voluntary contributions cannot be withdrawn while the loan is active.

### Can the employee-borrower renew his/her loan? If yes, when?

Yes, employee-borrower may renew his/her loan after paying at least 50% of the principal loan balance and this can be applied again through ### retirement tool. The current loan balance shall be deducted from the renewed loan proceeds.*### After employee-borrower fully pays the loan over the selected term, when can employee- borrower apply again for the member loan?

Employees who successfully complete their loan payments over the selected term can re- apply for a new loan immediately after the final payment is posted on the retirement portal.

### When can employees start applying for the member loan?

The Retirement Plan Member Loan Program will be available to all employees who are currently participating in the Voluntary Contributions starting April 1, 2025.

### If a loan application is disapproved can an employee reapply?

If a loan application is disapproved the employee can promptly submit a new application through the retirement portal. Please ensure that the uploaded Promissory Note is accurate, signed, and clearly legible for a smoother process.

### What are the reasons for a loan to be disapproved?

The only reason for loan disapproval is an issue found with the uploaded Promissory Note.

### What if an employee changes their mind about borrowing money from the fund? Can they still cancel the loan application?

If the loan application status in the retirement portal is "Saved," the employee can cancel the loan by clicking the trash icon. However, if the status is "For Approval," the employee must submit a cancellation request to the Employee Center.

### What happens if the employee/borrower resigns immediately or absconds 1 month after receiving the loan amount?

The loan balance will be deducted from the employee’s retirement benefit, offsetting the Voluntary Contributions. Any remaining amount will be recovered from the final pay. If insufficient, the final pay will remain negative.

</KNOWLEDGE_BASE>
"""

    # Log AI generation start
    ai_start_time = time.time()
    logger.info(f"[{request_id}] Starting AI generation with model: {model_name}")
    
    # Generate response with streaming
    def generate():
      try:
        # Add system prompt to the conversation
        system_content = types.Content(
          role="user",
          parts=[types.Part.from_text(text=system_prompt)]
        )
        full_conversation = [system_content] + formatted_messages
        
        # Create generation config
        generate_content_config = types.GenerateContentConfig(
          temperature=0.7,
          top_p=0.8,
          max_output_tokens=2048,
          safety_settings=safety_settings,
        )
        
        logger.info(f"[{request_id}] Generation config - Temperature: 0.7, Max tokens: 2048")
        
        # Generate streaming response
        full_response = ""
        input_tokens = 0
        output_tokens = 0
        chunk_count = 0
        
        logger.info(f"[{request_id}] Starting streaming response generation")
        
        for chunk in client.models.generate_content_stream(
          model=model_name,
          contents=full_conversation,
          config=generate_content_config,
        ):
          if chunk.text:
            full_response += chunk.text
            chunk_count += 1
            yield f"data: {json.dumps({'type': 'content', 'content': chunk.text})}\n\n"
        
        # Calculate metrics
        end_time = time.time()
        ai_end_time = time.time()
        total_latency = end_time - start_time
        ai_latency = ai_end_time - ai_start_time
        
        # Estimate token usage (rough approximation)
        input_tokens = len(system_prompt.split()) + sum(len(msg["content"].split()) for msg in recent_messages)
        output_tokens = len(full_response.split())
        
        cost = calculate_cost(input_tokens, output_tokens)
        
        # Log detailed performance metrics
        logger.info(f"[{request_id}] AI generation completed - Chunks received: {chunk_count}")
        logger.info(f"[{request_id}] Response length: {len(full_response)} characters")
        logger.info(f"[{request_id}] Response preview: {full_response[:200]}...")
        logger.info(f"[{request_id}] Performance metrics:")
        logger.info(f"[{request_id}]   - Total latency: {total_latency:.2f}s")
        logger.info(f"[{request_id}]   - AI generation latency: {ai_latency:.2f}s")
        logger.info(f"[{request_id}]   - Input tokens (estimated): {input_tokens}")
        logger.info(f"[{request_id}]   - Output tokens (estimated): {output_tokens}")
        logger.info(f"[{request_id}]   - Total tokens: {input_tokens + output_tokens}")
        logger.info(f"[{request_id}]   - Estimated cost: ${cost:.6f}")
        logger.info(f"[{request_id}]   - Tokens per second: {(input_tokens + output_tokens) / ai_latency:.2f}")
        
        # Send metrics
        metrics = {
          'type': 'metrics',
          'input_tokens': input_tokens,
          'output_tokens': output_tokens,
          'total_tokens': input_tokens + output_tokens,
          'cost': round(cost, 6),
          'latency': round(total_latency, 2),
          'ai_latency': round(ai_latency, 2),
          'chunk_count': chunk_count,
          'tokens_per_second': round((input_tokens + output_tokens) / ai_latency, 2)
        }
        
        yield f"data: {json.dumps(metrics)}\n\n"
        yield "data: [DONE]\n\n"
        
        logger.info(f"[{request_id}] Request completed successfully")
        
      except Exception as e:
        logger.error(f"[{request_id}] Error during AI generation: {str(e)}", exc_info=True)
        error_data = {'type': 'error', 'error': str(e)}
        yield f"data: {json.dumps(error_data)}\n\n"
    
    return Response(generate(), mimetype='text/plain')
    
  except Exception as e:
    logger.error(f"[{request_id}] Error in chat endpoint: {str(e)}", exc_info=True)
    logger.error(f"[{request_id}] Request data: {data if 'data' in locals() else 'No data available'}")
    return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
  logger.info("Health check requested")
  return jsonify({'status': 'healthy'})

if __name__ == '__main__':
  logger.info("Starting Optum HR Chat Application")
  logger.info(f"Model: {model_name}")
  logger.info(f"Pricing - Input: ${PRICING_PER_TOKEN['input']:.6f}/token, Output: ${PRICING_PER_TOKEN['output']:.6f}/token")
  app.run(debug=True, host='0.0.0.0', port=5001)
