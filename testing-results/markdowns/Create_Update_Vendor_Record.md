


Page 1 from document Create_Update_Vendor_Record

## vendors@gov## Vendor Record User GuideA guide to create, view and update vendor record details at Vendors@Gov.GYD



Page 2 from document Create_Update_Vendor_Record

## vendors@gov## Vendor Record User GuideSelect the topics below to learn more about:## 1. Create Vendor RecordNew vendors will be directed to 'Create New Vendor' page to create a vendor record.2. View/ Update Vendor Record Details## 2. View/ Update Vendor Record DetailsExisting vendor may navigate to 'Update Vendor Details' to  update your name, contact, GST registration and bank details.## 3. Vendor Record StatusVendor record status include Approved, Unapproved, Inactive.1. Create Vendor Record3. Vendor Record StatusGYD



Page 3 from document Create_Update_Vendor_Record

## 1. Create Vendor Record
IMAGE FOUND, DESCRIPTION : - Title / header area:
  - “Get started by logging in.” (primary heading)
  - Subtext line: “Click here if you do not have an account” (here hyperlinked indicator)

- User option cards (top section):
  - Card 1: “For Business Users” with subheading “Login with Singpass”
  - Card 2: “For Individual Users” with subheading “Login with Singpass”
  - Each card has rounded rectangle white background with drop shadow
  - Card 1 alignment: left; Card 2 alignment: right

- Secondary links (under the three main blocks):
  - Text: “For Local & Foreign Entities” (blue link)
  - Text: “For Individuals” (blue link)
  - Text: “Click here if you are a foreign individual with an AGD Password” (blue link)

- Main visual area:
  - Large illustration of an invoice document with the word “INVOICE” prominently displayed at the top-left of the document
  - Sub-elements on the invoice include multiple callout bubbles with text:
    - Bubble 1 (near left): “Submit Invoices”
    - Bubble 2 (center): “Update Vendor Details”
    - Bubble 3 (left, near bottom): “Monitor Payment Status”
  - A person figure standing left of the invoice interacting with the document
  - Another seated person figure on the right holding a circular icon with a dollar sign
  - Cartoon trees/foliage in yellow and orange color on the right side as decorative background

- Iconography and actions:
  - Central large cloud-like button or bubble near the invoice with no explicit label visible
  - Visual emphasis on payment and vendor management processes

- Overall layout semantics:
  - Top navigation/intro area with user-type login options
  - Informational/CTA area featuring an invoice workflow with three primary actions
  - Graphical illustration conveying invoice processing, payment monitoring, and vendor details update
  - Color palette: cool grays/blues with accent colors for bubbles and decorative trees

- Data primitives suitable for vector indexing:
  - Entities: UserType (For Business Users, For Individual Users), LoginMethod (Login with Singpass)
  - Actions (Invoice-related): Submit Invoices, Update Vendor Details, Monitor Payment Status
  - Document: INVOICE
  - Roles: Local & Foreign Entities, Individuals
  - Visual elements: Hero image (invoice doc with bubbles), two human figures, currency symbol, decorative trees

- Relationships / flow:
  - User selects a UserType (Business or Individual) to login via Singpass
  - Access route links presented for local/foreign entities or individuals
  - Invoice workflow relationship: Submit Invoices -> (implied) generate/monitor status -> Update Vendor Details
  - Payment flow: Currency symbol suggests monetary transactions and payment status monitoring

- Notable text blocks (for indexing):
  - Get started by logging in.
  - Click here if you do not have an account
  - For Business Users — Login with Singpass
  - For Individual Users — Login with Singpass
  - For Local & Foreign Entities
  - For Individuals
  - Click here if you are a foreign individual with an AGD Password
  - INVOICE
  - Submit Invoices
  - Update Vendor Details
  - Monitor Payment Status

- Visual metadata:
  - Page/scene: Login and invoice processing splash screen
  - Imagery: Invoice document graphic with three blue chat-bubbles/labels
  - Calls-to-action: Login options, CTA bubbles on invoice

- Structure for database serialization:
  - Scene: UserLoginAndInvoiceWorkflow
  - Nodes: 
    - Node: UserLoginOptionBusiness (label: “For Business Users”, method: “Login with Singpass”)
    - Node: UserLoginOptionIndividual (label: “For Individual Users”, method: “Login with Singpass”)
    - Node: LocalAndForeignEntitiesLink (label: “For Local & Foreign Entities”)
    - Node: IndividualsLink (label: “For Individuals”)
    - Node: AGDPasswordInfoLink (label: “Click here if you are a foreign individual with an AGD Password”)
    - Node: InvoiceDocument (label: “INVOICE”)
    - Node: SubmitInvoicesAction (label: “Submit Invoices”)
    - Node: UpdateVendorDetailsAction (label: “Update Vendor Details”)
    - Node: MonitorPaymentStatusAction (label: “Monitor Payment Status”)
    - Node: CurrencySymbolIcon (label: “$”)
  - Edges / Flows:
    - UserLoginOptionBusiness -> InvoiceDocument (via login flow)
    - UserLoginOptionIndividual -> InvoiceDocument (via login flow)
    - InvoiceDocument -> SubmitInvoicesAction
    - InvoiceDocument -> UpdateVendorDetailsAction
    - InvoiceDocument -> MonitorPaymentStatusAction
  - Annotations:
    - Scene purpose: authentication gateway with invoice processing workflow visualization
    - Visual cues: blue bubbles denote actions; currency icon indicates payments

Getstarted by loggingin.Clickhere if you do nothave anaccountFor BusinessForIndividualUsersUsersLoginwithSingpassLoginwithSingpassForLocal &amp;Foreign EntitiesForIndividualsClickhere ifyouareaforeignindividualwithanAGDPasswordINVOICESubmitinvoicesMonitorUpdatePayment StatusVendorDetailsLogin to Vendors@Gov portal (www.vendors.gov.sg).For more information on how to login, please refer to' Vendors@Gov Login User Guide '.



Page 4 from document Create_Update_Vendor_Record

## 1. Create Vendor RecordIf you are a new vendor, you will be directed to ' Create New Vendor ' page.Home》CreateNewVendorCreate NewVendorAuthorisationVendor DetailsBank DetailsSummaryComplete## Authorisation1. I/We hereby authorise the Government and Statutory Boards to credit payments due to me/us to the stated account. Amounts so credited would constitute valid discharge of obligations due to me/us.2. This authorisation shall continue to be in force until I/we have notified you in writing.3. I/We hereby request and authorise the Government and Statutory Boards to obtain confirmation/ verification of information relating to me/us and/or to my/our account(s) from/with the bank where the Account is maintained as stated in the form.



Page 5 from document Create_Update_Vendor_Record

## 1. Create Vendor RecordVendorID1Official NameVendor ID is not editable.The vendor ID is a unique identifier that identifies your vendor record. The vendor ID is assigned as follows:## Company/ Organisation- UEN Registered Entity -The vendor ID will be your organization's UEN.- Foreign Entity -The vendor ID will be your Corppass Entity ID/ GeBIZ trading partner reference.## Individual- NRIC/ FIN Holder -The vendor ID will be your NRIC/ FIN.- Non-NRIC/ FIN Holder -The vendor ID will be your passport number.The vendor ID may appear incorrectly if you have selected the wrong login option.VendorName*



Page 6 from document Create_Update_Vendor_Record

## 1. Create Vendor Record (Individuals with Singpass)VendorID2Vendor Name *Vendor name is retrieved from Government database- MyInfo and is not editable## Individuals with Singpass- Your name will be auto-populated from the government database - MyInfo hence, it will not be allowed for edit.If the name which was reflected at the Vendor Name field is inaccurate, you may wish to verify your name registered at MyInfo/ICA.



Page 7 from document Create_Update_Vendor_Record

## 1. Create Vendor Record (Local Companies)Official name registered and retrieved from the government database - Enterprise Data Hub (EDH)First 80 characters is populated from your official name.VendorIDOfficialNameVendorName*2Vendor name is retrieved from Government database - Enterprise Datahub (EDH) and is not editable## UEN Registered Company/ Organisation- Your name will be auto-populated from the government database-Enterprise Datahub (EDH), hence, it will not be allowed for edit.Do note that only the first 80 characters are retrieved and displayed under the vendor name field.If the name which was reflected at the Vendor Name field is inaccurate, you may wish to verify your name registered at your UEN issuance agency.



Page 8 from document Create_Update_Vendor_Record

## 1. Create Vendor Record (Foreign Companies)Name that is retrieved fromCorppassFirst 80 characters retrievedfrom CorppassVendorIDCorppass NameVendorName2Name is retrieved from Corppass and is not editable## Non-UEN Registered Company/ Organisation- Your company name will be auto-populated according to your Corppass registered name.If the name which was reflected at the Vendor Name field is inaccurate, you may wish to contact Corppass.Do note that only the first 80 characters are retrieved and displayed under the vendor name field.



Page 9 from document Create_Update_Vendor_Record

## 1. Create Vendor Record - Contact Details
IMAGE FOUND, DESCRIPTION : - Section: Contact Details
  - Field: Email Address *
    - Type: text input
    - Placeholder/Note: none shown
  - Field: Contact No. *
    - Type: text input
    - Placeholder/Note: none shown

- Section: Address
  - Subsection: Country *
    - Type: dropdown/select
    - Placeholder/Note: none shown
  - Subsection: Postal Code *
    - Type: text input
  - Subsection: State
    - Type: dropdown/select
    - Placeholder/Note: “Please Select”
  - Subsection: City *
    - Type: text input
    - Current value: “SINGAPORE” (uppercase)
  - Subsection: Address *
    - Type: row of text inputs
      - Input 1: text field
      - Input 2: text field
      - Input 3: text field
      - Input 4: text field

- UI Action:
  - Button: Clear Address Fields
  - Button Type/Style: blue fill with white text, positioned to the right of the Address section header

- Visual/layout notes:
  - The form is contained within an orange-outlined boundary.
  - Section headers are bolded, with a clean, two-column layout for the top fields and a multi-field row for the address inputs.
Contact DetailsEmuil Addrers *Contact No. *AddressClearAddress FieldsCountry *Postal Code *StateCityPlease SelectSINGAPOREAddrem"Hext- Your Contact Details and Address will be populated from MyInfo for individuals and EDH for companies. However, you may amend your details if they are inaccurately reflected. To amend your address, you may click on the 'Clear Address' button 3- Email address: All Vendors@Gov updates and softcopy remittance advices will be sent to this email address. Only one email address is allowed for each vendor record.- Contact No.: Please provide/verify your contact information.- ·- Country, Postal Code, State, City, Address: Company/ Organisation -Please provide/verify your business registered address. Individual -Please provide/verify your residential address. *Your address will be auto-populated according to the postal code you have input for Singapore addresses. After you have entered the contact details and address, click on 'Next' to proceed to the bank details page.



Page 10 from document Create_Update_Vendor_Record

## 1. Create Vendor Record - Bank Details## BankDetailsPaymentMethod*Inter-BankGIRO- [ ] PayNow- [ ] TelegraphicTransfer4Select your payment mode and enter your bank details.Payment Mode:Inter-Bank Giro (IBG) -Select this option if you are receiving Singapore dollars (SGD) payment with a local bank account.Paynow (PAYN) -Select this option if you are receiving Singapore dollars (SGD) payment via PayNow. Please ensure that all agencies you are transacting with are PayNow ready.Telegraphic Transfer (TT) -Select this option if you are receiving:- a) Foreign currency payment; or- b) Singapore dollars (SGD) payment with a foreign bank account.## NOTE- IBG option is not available for foreign vendors. Foreign vendor may submit a hardcopy Direct Credit Authorisation (DCA) form with bank endorsement to AGD and subsequently lodge a helpdesk ticket for assistance to update your IBG bank details.- PAYN option is sole payment mode for SGD payments to CAYE-eligible self-employed vendors.- TT  option is  not  available  for  vendors  who  are  transacting  as  an  individual.  Individuals  may  lodge  a  helpdesk  ticket  for assistance to update your TT bank details.YourVendorID:



Page 11 from document Create_Update_Vendor_Record

## 1. Create Vendor Record - Bank Details (IBG)
IMAGE FOUND, DESCRIPTION : Bank Details

Payment Method *
- Inter-Bank GIRO (selected)
- PayNow
- Telegraphic Transfer

Bank Details (outlined orange box)
- Bank *: [Drop-down] Please Select Bank…
- Branch *: [Drop-down/input] 
- Account Number *: [Text input]

GST Registered *
- Yes (selected)
- No

GST Registration Number *: [Text input]

Next action controls (bottom right)
- Back (gray button)
- Next (blue button)
## BankDetailsYour Vendor IDPaymentMethod*Inter-Bank GIRO- [ ] PayNowTelegraphic TransferBonk *BrunchAecount Number .--Pleuse Select Dank--GST Registered *GST Registration NumberYesNoBackNert## Inter-Bank Giro (IBG) option selected.Select your bank and branch code, enter your account number.The bank account provided must be registered under the entity's name and ID. Bank details (Eg: Bank &amp; Branch code, Bank account) must be updated correctly. If you are unsure of your bank details, please contact your bank to confirm the correct information.Company/  Organization -You  should  provide  a  corporate  bank  account  that  is  registered  under  your  business registration name and ID (Eg: UEN).Individuals -You should provide a bank account that is registered under your personal name and ID (Eg: NRIC, FIN or Passport no.).



Page 12 from document Create_Update_Vendor_Record

## 1. Create Vendor Record - Bank Details (IBG)
IMAGE FOUND, DESCRIPTION : - Section: Bank Details
- Payment Method (required): Inter-Bank GIRO selected (radio)
  - Other options (unselected): PayNow, Telegraphic Transfer
- Bank (required): dropdown with placeholder “Please Select Bank…”
- Branch (required): text/input field (empty)
- Account Number (required): text/input field (empty)
- GST Registered (required): Yes selected (radio), No option unselected
- GST Registration Number (required): text/input field (empty) adjacent to the GST Registered row
- Layout cues: fields arranged in a multi-column form; GST-related section highlighted with orange border, and the Inter-Bank GIRO option highlighted with orange border
- Actions: Back button (left), Next button (right) positioned at bottom-right
- UI notes: Vendor ID label at top-right.
BankDetailsYour Vendor ID:PaymentMethod*Inter-Bank GIROPayNowTelegraphic TransferBankBranch *Account Number--Pleuse Select Dank-GST Registered *GST Registration Number *YesNoBackNert## Inter-Bank Giro (IBG) option selected.## Select your GST registration status.- If you are GST Registered, please select 'Yes' for GST Registered option. Then, enter your GST registration number (Please enter only the numbers and omit the ' -' dash).- If you are not GST Registered, please select 'No' for GST Registered option' .NOTEGST registration update is not available for vendors who have registered a TT bank account. To update your GST registration details, please lodge a helpdesk ticket for assistance.



Page 13 from document Create_Update_Vendor_Record

## 1. Create Vendor Record - Bank Details (IBG)
IMAGE FOUND, DESCRIPTION : - Form layout description:
  - Bank field: labeled "Bank *" with a dropdown placeholder "Please Select Bank" and a down-arrow indicator suggesting a select box.
  - Branch field: labeled "Branch *" with a dropdown/select box (no placeholder visible).
  - Account Number field: labeled "Account Number *" with a text input box (single line).
  - GST Registered field: labeled "GST Registered *" with two radio options:
    - Yes (selected)
    - No (unselected)
  - GST Registration Number field: labeled "GST Registration Number *" with a single-line text input box.
- Action buttons (aligned to the bottom-right):
  - Back button: gray, labeled "Back".
  - Next button: blue, labeled "Next", with an orange border emphasis around the button.
- Logical flow:
  - User selects Bank → Branch → enters Account Number → selects GST Registered (Yes/No) → if applicable enters GST Registration Number → proceeds by pressing Next.
  - The Back button navigates to the previous screen. The Next button advances to the following screen.
BankBranchAecount Number--Pleose Select DankGST Registered*GST Registration NumberYesNoBackNent## Inter-Bank Giro (IBG) option selected.After updating your payment details, click 'Next' and on the summary page, click 'Next' again to submit your vendor record request. Once approved, you will receive an email notification at your registered email address.



Page 14 from document Create_Update_Vendor_Record

## 1. Create Vendor Record - Bank Details (PayNow)
IMAGE FOUND, DESCRIPTION : - Bank Details section
  - Payment Method (required)
    - Options: Inter-Bank GIRO, PayNow (selected), Telegraphic Transfer
- Orange-outlined Proxy Details block
  - Proxy Type (required): Dropdown with placeholder option "--Please Select Proxy Type--"
  - Proxy Value (required): Text input field
- GST Registered (required)
  - Options: Yes, No
- GST Registration Number
  - Value: N.A.
- Status message: "PayNow (PAYN) option selected." (orange banner)
## PayNow  (PAYN) option selected.Bank DetailsPayment Method *Ihter-Bank GIROPayNowTelegraphic TranslerProxy TypeProxy Value--Plesse Select Proxy Type--GST Registered*GST Registration Number*YesNoN.A.YourVendoriSelect your proxy type and enter your proxy value. The PayNow proxy value refers to the unique indicator of the recipient which  may be used to receive payments via PayNow.- PayNow proxy should be within 8 to 17 characters.- Acceptable PayNow proxy values are as follows:- Individuals: NRIC/FIN Number (e.g. S1234567X)- Corporates: UEN (e.g. 201234567A) or UEN + 3-character suffix (e.g. 201234567A B12 , 201234567A 321 ), where a 3-character alphanumeric suffix can be added to your company's UEN to create multiple PayNow proxies. This is based off what proxy is registered with your bank and the respective bank account.Important:  Please  ensure that  your  bank  account  is  correctly  linked  with  the  PayNow  proxy  provided  to  avoid  payment errors. This can usually be done via the bank's iBanking website or mobile application. For clarifications on linking your PayNow proxy to your bank account, please contact your bank.



Page 15 from document Create_Update_Vendor_Record

## 1. Create Vendor Record - Bank Details (PayNow)Bank DetailsPayment Method *Ihter-Bank GIROPayNowTelegraphic TranslerProxy Type *Proxy Value *--Plese Select Proxy Type--GST Registered *GST Registration Number *NoN.A.## PayNow  (PAYN) option selected.## Select your GST registration status.- If you are GST Registered, please select 'Yes' for GST Registered option. Then, enter your GST registration number (Please enter only the numbers and omit the ' -' dash).- If you are not GST Registered, please select 'No' for GST Registered option' .YourVendori



Page 16 from document Create_Update_Vendor_Record

## 1. Create Vendor Record - Bank Details (TT)
IMAGE FOUND, DESCRIPTION : Bank Details section (Telegraphic Transfer selected)

Payment Method
- Options: Inter-Bank GIRO, PayNow, Telegraphic Transfer (selected)

Form fields within the orange-bordered area:
- Country of Bank: drop-down select (default placeholder “Select Bank Country”)
- Bank Name: text input
- Swift ID: text input
- Account Number: text input
- Bank Address: text input (multi-line layout area)
- Clearing Code: text input
- Routing Code: text input
- Payment Details: text input
- Corresponding Bank Required: radio group with Yes / No (default likely No)

Additional UI elements:
- Your Vendor ID (display area in the top-right corner)

Notes:
- The Telegraphic Transfer option is currently highlighted/selected.
- The fields are arranged in a two-row grid within the orange outline, with the top row containing Country of Bank, Bank Name, Swift ID, and Account Number; the second row containing Bank Address and Clearing Code; and a lower row containing Routing Code and Payment Details. The “Corresponding Bank Required” field uses a Yes/No radio pair.
BankDetailsourVendor ID;PaymentMethodInter-BankGIROPayNowTelegraphicTransferCouniryal DankurkHomH!SaltID!Aarwunt Mumbe OCearig Cod Okoutng Coie OPymn Deuh oComsponding Bank RacuiridYiHo## Telegraphic Transfer (TT) option selected.Enter your TT bank details.The bank account provided must be registered under your entity's name with the bank.Please ensure to provide the correct bank details to avoid payment rejection by the bank. If you are unsure of your bank details, please contact your bank to confirm the information for your remittance transfer.



Page 17 from document Create_Update_Vendor_Record

## 1. Create Vendor Record - Bank Details (TT)
IMAGE FOUND, DESCRIPTION : - Section: Bank Details
- Payment Method options (radio group): 
  - Inter-Bank GIRO (not selected)
  - PayNow (not selected)
  - Telegraphic Transfer (TT) (selected)
- TT subsection framed in orange box (form fields grid):
  - Country of Bank: dropdown “-Select Bank Country-”
  - Bank Name: text input (required)
  - Swift ID: text input (required)
  - Account Number: text input (required)
  - Bank Address: text input
  - Clearing Code: text input
  - Routing Code: text input
  - Payment Details: text input
  - Corresponding Bank Required: radio options Yes / No (default No: No selected or not specified)
- Right panel header: “Telegraphic Transfer (TT) option selected.”
- Instruction block (right column, informational):
  - After updating the bank details, click Next and on the summary page, click Next again to submit your vendor record request.
  - You can only submit e-Invoices after your vendor record has been approved.
  - Note icon block: 
    - Update of Telegraphic Transfer (TT) bank details function is not available for local/foreign vendors who are transacting as an individual. To update your TT bank details, please lodge a helpdesk ticket. (with a hyperlink labeled "helpdesk ticket")
  - GST registration update is not available for vendors who have registered a TT bank account. To update your GST registration details, please lodge a helpdesk ticket for assistance. (with a hyperlink labeled "helpdesk ticket")
Update  of  Telegraphic  Transfer  (TT)  bank  details function  is  not  available  for  local/foreign  vendors who  are  transacting  as  an    individual.  To  update your  TT  bank  details,  please  lodge  a  helpdesk ticket.GST registration update is not available for vendors who have registered a TT bank account. To update your GST registration details, please lodge a helpdesk ticket  for assistance.## Telegraphic Transfer (TT) option selected.After updating the bank details, click 'Next' and on the  summary  page,  click 'Next' again  to  submit your vendor record request.You can only submit e-Invoices after your vendor record has been approved.## Bank DetailsPayment Method *Inter-Bank GiROPayNowTelegraphic TransferCountryof BlankSwiftID"Stecx BankCoumryDank Address'ClearingCodeNOTEtoutingCodPaymentDeais



Page 18 from document Create_Update_Vendor_Record

## vendors@gov## Vendor Record User GuidesSelect the topics below to learn more about:## 1. Create Vendor RecordNew vendors will be directed to 'Create New Vendor' page to create a vendor record.2. View/ Update Vendor Record Details## 2. View/ Update Vendor Record DetailsExisting vendor may navigate to 'Update Vendor Details' to  update your name, contact, GST registration and bank details.## 3. Vendor Record StatusVendor record status include Approved, Unapproved, Inactive.1. Create Vendor Record3. Vendor Record StatusGYD



Page 19 from document Create_Update_Vendor_Record

## 2. View/ Update Vendor Record Details
IMAGE FOUND, DESCRIPTION : - Overall layout: An illustrated onboarding/invoice processing infographic. Title area at top with “Get started by logging in.” followed by two parallel callouts and a large invoice illustration occupying the lower two-thirds.

- Top navigation/help text:
  - Primary header: “Get started by logging in.”
  - Subheader: “Click here if you do not have an account” (with the word “here” styled as a hyperlink).

- User-type choice section (two rounded white cards with shadows, aligned horizontally):
  - Card 1 (blue accent for business users): 
    - Heading: “For Business Users”
    - Subheading: “Login with Singpass”
  - Card 2 (red accent for individual users): 
    - Heading: “For Individual Users”
    - Subheading: “Login with Singpass”

- Secondary help/links line (under the two cards):
  - Left-aligned: “For Local & Foreign Entities”
  - Right-aligned: “For Individuals”
  - Small link text: “Click here if you are a foreign individual with an AGD Password” (with “here” as hyperlink)

- Central illustration:
  - Large stylized document labeled “INVOICE” with a folded corner at top-right.
  - Three floating callout bubbles overlaying the invoice:
    - Bubble A (left): “Monitor Payment Status”
    - Bubble B (center): “Submit Invoices”
    - Bubble C (center-right): “Update Vendor Details”
  - Foreground figures:
    - A standing male figure to the left interacting with the document.
    - A seated person on the ground to the right, holding a circular object with a dollar sign.
  - Decorative elements: two stylized trees (one yellow/orange, one orange/red) on the right side.

- Data/interaction semantics:
  - User authentication routes for two user cohorts: business users and individual users, each via Singpass login.
  - Additional modules suggested by callouts: 
    - Invoice submission (Submit Invoices)
    - Invoice status monitoring (Monitor Payment Status)
    - Vendor data management (Update Vendor Details)
  - Contextual navigation/help: links to account creation, entity-specific guidance, and AGD password assistance.

- Visual style attributes (for indexing):
  - Color cues: blue for business, red for individual.
  - UI elements: rounded cards with drop shadows; large header “INVOICE” with folded-page motif.
  - Interaction hints: speech-bubble style callouts, user icons, and currency symbol graphic.
Getstarted bylogging in.Clickhere if you donothave an accountFor BusinessForIndividualUsersUsersLoginwithSingpassLoginwithSingpassForLocal&amp;Foreign EntitiesForIndividualsClickhere ifyouare a foreign individual with anAGDPasswordINVOICESubmitinvoicesMonitorUpdatePayment StatusVendorDetailsLogin to Vendors@Gov portal (www.vendors.gov.sg).For more information on how to login, please refer to ' Vendors@Gov Login andRegistration User Guide '.



Page 20 from document Create_Update_Vendor_Record

## 2. View/ Update Vendor Record DetailsFor existing vendor, please navigate to ' Update Vendor Details ' to view or update your vendor record details.
IMAGE FOUND, DESCRIPTION : - Left navigation panel:
  - Home (icon: house)
  - E-Invoice (icon: document)
    - Create E-Invoice
    - Upload Batch E-Invoices
    - Upload Attachment
  - View Invoicing Instructions
  - Update Vendor Details (orange highlighted selection)

- Main content header (top action/tabs):
  - All Invoices: count 4
  - Draft: count 0
  - Submitted: count 4
  - Processing: count 0
  - Approved: count 0
  - Paid: count 0
  - Rejected: count 0
  - Additional vertical ellipsis menu on far right

- Sub-header table row (data grid header):
  - Columns (left to right):
    - S/No.
    - Status (with small triangle/indicator)
    - Invoice No.
    - Invoice Date
    - Client Agency
    - Currency
    - Invoice Amount
    - Actions (checkbox or action control)

- Data grid body:
  - Repeated rows of invoice entries with uniform hashed/blurred content indicating multiple rows; placeholders correspond to the values for each column (serial, status, invoice number, date, client agency, currency, amount, and available actions).
  - Visual styling consistent with a tabular invoice list: alternating light gray rows, dense horizontal separators.

- Functional notes:
  - The UI represents an e-invoice management module with a tabbed summary of invoice states and a detailed list grid beneath, enabling per-invoice actions via the Actions column.
  - The left panel’s highlighted “Update Vendor Details” indicates the current focus or selected feature.
Home &gt;函4这00E-Invoice &gt;All InvoicesDraftSubmittedProcessingApprovedPaidRejected&gt;Create E-lnvoiceINVOICEINVOICE&gt;UploadBatchE-lnvoicesS/NO.STATUSINVOICENO.DATECLIENTAGENCYCURRENCYAMOUNTACTIONS&gt; Upload AttachmentView Invoicing InstructionsUpdate VendorDetails&gt;



Page 21 from document Create_Update_Vendor_Record

## 2. View/ Update Vendor Record DetailsVendor ID1Vendor Name * 0Vendor Record StatusApprovedUpon each login, vendor name is retrieved from Government database- MyInfo and is not editable## Individuals with Singpass- Your name will be auto-populated from the government database - MyInfo hence, it will not be allowed for edit.If the name which was reflected at the Vendor Name field is inaccurate, you may wish to verify your name registered at MyInfo/ICA.In the unlikely event where the connectivity to the government database fails, the name field will then be available for updating. However, if you choose not to do the manual update, your name will be retrieved from MyInfo when the connectivity is restored.



Page 22 from document Create_Update_Vendor_Record

## 2. View/ Update Vendor Record Details (Local Companies)Official name registered and retrieved from the government database - Enterprise Data Hub (EDH)First 80 characters is populated from your official name.VendorIDOfficial NameVendor Name*VendorRecordStatusApproved1Upon each login,  vendor  name  is  retrieved  from  Government  database  -  Enterprise  Datahub  (EDH)  and  is  not editable## UEN Registered Company/ Organisation- Your name will be auto-populated from the government database-Enterprise Datahub (EDH), hence, it will not be allowed for edit.Do note that only the first 80 characters are retrieved and displayed under the vendor name field. If the name which was reflected at the Vendor Name field is inaccurate, you may wish to verify your name registered at your UEN issuance agency.In the unlikely event where the connectivity to the government database fails, the name field will then be available for updating. However, if you choose not to do the manual update, your name will be retrieved from EDH when the connectivity is restored.



Page 23 from document Create_Update_Vendor_Record

## 2. View/ Update Vendor Record Details (Foreign Companies)Name that is retrieved fromCorppassFirst 80 characters retrievedfrom CorppassVendorIDCorppass NameVendorNameVendorRecordStatusApproved1Vendor name is retrieved from Corppass and is not editable## Non-UEN Registered Company/ Organisation- Your company name will be auto-populated according to your Corppass registered name.If the name which was reflected at the Vendor Name field is inaccurate, you may wish to contact Corppass.Do note that only the first 80 characters are retrieved and displayed under the vendor name field.



Page 24 from document Create_Update_Vendor_Record

## 2. View/ Update Vendor Record Details - Contact Details
IMAGE FOUND, DESCRIPTION : - Form Section: Contact Details
  - Fields:
    - Email Address (required)
    - Contact No. (required)

- Form Section: Address
  - Subsection: Location Details
    - Country (required): dropdown selector
    - Postal Code (required): text input
    - State: dropdown selector (default option shown: Please Select)
    - City (required): text input (pre-filled value shown: SINGAPORE)
  - Subsection: Street Address
    - Address (required): four individual text inputs arranged in a single row (likely addressing multiple address lines: Address 1, Address 2, Address 3, Address 4 as placeholders)

- Layout/flow notes:
  - All fields labeled with asterisk denote required.
  - City field shows a default or preselected value of SINGAPORE.
  - State and Country are dropdown controls, indicating standardized value sets.
  - The design presents two main form groups: Contact Details and Address (with subfields for Country, Postal Code, State, City, and multi-line Address).
Contact DetailsEmail Address *Contact No.AddressCountry *Postal Code *StateCityPlease SelectSINGAPOREAddrem"Hext2Update your Contact Details and Address.- Email address: All  Vendors@Gov updates and softcopy remittance advices will be sent to this email address. Only one email address is allowed for each vendor record.- Contact No.: Please provide your contact information.- Please provide your business registered address.- Country, Postal Code, State, City, Address: Company/ Organisation Individual -Please provide your residential address.After you have entered the contact details and address, click on 'Next' to proceed to the bank details page.



Page 25 from document Create_Update_Vendor_Record

## 2. View/ Update Vendor Record Details - Bank Details## BankDetailsPaymentMethod*- [x] Inter-BankGIRO- [ ] PayNow- [ ] TelegraphicTransfer4Select your payment mode and enter your bank details.Payment Mode:Inter-Bank Giro (IBG) -Select this option if you are receiving Singapore dollars (SGD) payment with a local bank account.Paynow (PAYN) -Select this option if you are receiving Singapore dollars (SGD) payment via PayNow. Please ensure that all agencies you are transacting with are PayNow ready.Telegraphic Transfer (TT) -Select this option if you are receiving:- a) Foreign currency payment; or- b) Singapore dollars (SGD) payment with a foreign bank account.## NOTE- IBG option is not available for foreign vendors. Foreign vendor may submit a hardcopy Direct Credit Authorisation (DCA) form with bank endorsement to AGD and subsequently lodge a helpdesk ticket for assistance to update your IBG bank details.- PAYN option is sole payment mode for SGD payments to CAYE-eligible self-employed vendors.- TT  option is  not  available  for  vendors  who  are  transacting  as  an  individual.  Individuals  may  lodge  a  helpdesk  ticket  for assistance to update your TT bank details.YourVendorID:



Page 26 from document Create_Update_Vendor_Record

## 2. View/ Update Vendor Record Details - Bank Details (IBG)
IMAGE FOUND, DESCRIPTION : - Document type: Bank Details form (UI screen for payment setup)

- Payment Method section (mandatory field indicator "*"):
  - Options (radio buttons):
    - Inter-Bank GIRO (selected)
    - PayNow
    - Telegraphic Transfer

- Bank Details section (outlined with orange border):
  - Bank* (dropdown): Label suggests a select list with placeholder "Please Select Bank..."
  - Branch* (dropdown): Empty input field next to Bank
  - Account Number* (text input): Single-line input field with placeholder
  - The three fields are positioned on a single row within the orange outline

- GST Registered* (radio button group):
  - Options:
    - Yes (selected)
    - No

- GST Registration Number* (text input): Empty single-line input field next to the GST status row

- Action buttons (bottom right):
  - Back (gray button)
  - Next (blue button)

- Visual notes:
  - “Your Vendor ID” label appears in the top-right corner with a blurred/obfuscated value.
  - Overall layout uses left-aligned labels with corresponding input controls to the right; required fields are marked with an asterisk.

- Datapoints and keys for database indexing:
  - payment_method: "Inter-Bank GIRO" (default selected)
  - bank: [string] (selected from dropdown; placeholder text: "Please Select Bank...")
  - branch: [string] (dropdown)
  - account_number: [string]
  - gst_registered: true
  - gst_registration_number: [string]
  - vendor_id: [obfuscated value]
BankDetailsYour Vendor IDPaymentMethod*Inter-Bank GIRO- [ ] PayNowTelegraphic TransferBonk *BrunchAecount Number .--Pleuse Select Dank--GST Registered *GST Registration NumberYesNoBackNert## Inter-Bank Giro (IBG) option selected.Select your bank and branch code, enter your account number.The bank account provided must be registered under the entity's name and ID. Bank details (Eg: Bank &amp; Branch code, Bank account) must be updated correctly. If you are unsure of your bank details, please contact your bank to confirm the correct information.Company/  Organization -You  should  provide  a  corporate  bank  account  that  is  registered  under  your  business registration name and ID (Eg: UEN).Individuals -You should provide a bank account that is registered under your personal name and ID (Eg: NRIC, FIN or Passport no.).



Page 27 from document Create_Update_Vendor_Record

## 2. View/ Update Vendor Record Details - Bank Details (IBG)
IMAGE FOUND, DESCRIPTION : - Section: Bank Details
  - Payment Method * (required)
    - Inter-Bank GIRO (selected)
    - PayNow (not selected)
    - Telegraphic Transfer (not selected)
- Fields (layout in two-row form):
  - Bank * (dropdown): “Please Select Bank”
  - Branch * (text field or dropdown)
  - Account Number * (text field)
- GST Registered * (required)
  - Yes (selected)
  - No (not selected)
- GST Registration Number * (text field)
- Action Buttons:
  - Back (disabled/implied)
  - Next (enabled)
BankDetailsYour Vendor IDPaymentMethod*Inter-Bank GIROPayNowTelegraphic TransferBankBrunchAccount Number--Pleuse Select Dank-GST Registered *GST Registration Number *YesNoBackNert## Inter-Bank Giro (IBG) option selected.## Select your GST registration status.- If you are GST Registered, please select 'Yes' for GST Registered option. Then, enter your GST registration number (Please enter only the numbers and omit the ' -' dash).- If you are not GST Registered, please select 'No' for GST Registered option' .NOTEGST registration update is not available for vendors who have registered a TT bank account. To update your GST registration details, please lodge a helpdesk ticket for assistance.



Page 28 from document Create_Update_Vendor_Record

## 2. View/ Update Vendor Record Details - Bank Details (IBG)
IMAGE FOUND, DESCRIPTION : - Bank: Dropdown field with placeholder text "Please Select Bank" (required)
- Branch: Dropdown field (required)
- Account Number: Text input field (required)
- GST Registered: Radio group with options: Yes (selected) and No
- GST Registration Number: Text input field (required)
- Next action: Primary action button labeled "Next" (outlined/blue) on the bottom-right; a secondary action button labeled "Back" (gray) to its left

Layout relationships and flow:
- User selects a bank from Bank dropdown.
- User selects a branch from Branch dropdown.
- User enters an account number in the Account Number field.
- User indicates GST registration status via the Yes/No radio group.
- If GST registered is Yes, user enters GST Registration Number.
- User proceeds by clicking the "Next" button; the "Back" button allows returning to the previous step.
BankBranchAecount Number--Pleose Select DankGST Registered*GST Registration NumberYesNoBackNent## Inter-Bank Giro (IBG) option selected.After updating your payment details, click 'Next' and on the summary page, click 'Next' again to submit your vendor record request.Once approved, you will receive an email notification at your registered email address.



Page 29 from document Create_Update_Vendor_Record

## 2. View/ Update Vendor Record Details - Bank Details (PayNow
IMAGE FOUND, DESCRIPTION : - Section: Bank Details
- Payment Method (required): 
  - Inter-Bank GIRO (radio option, not selected)
  - PayNow (radio option, selected) [highlighted orange box around this option]
  - Telegraphic Transfer (radio option, not selected)

- Proxy Details (within orange-framed card)
  - Proxy Type * (dropdown): options include “--Please Select Proxy Type--” (default placeholder)
  - Proxy Value * (text input): single-line text field (empty)

- GST Registered * (radio group)
  - Yes (radio option, not selected)
  - No (radio option, not selected)

- GST Registration Number * (text field): shows “N.A.” (not applicable)

- Footer note: “PayNow (PAYN) option selected.” (orange banner at bottom)
## PayNow  (PAYN) option selected.Bank DetailsYourVendoriPayment Method *Ihter-Bank GIROPayNowTelegraphic TranslerProxy Type *Proxy Value *--Plese Select Proxy Type--GST Registered *GST Registration Number *YesNoN.A.Select your proxy type and enter your proxy value. The PayNow proxy value refers to the unique indicator of the recipient which  may be used to receive payments via PayNow.- PayNow proxy should be within 8 to 17 characters.- Acceptable PayNow proxy values are as follows:- Individuals: NRIC/FIN Number (e.g. S1234567X)- Corporates: UEN (e.g. 201234567A) or UEN + 3-character suffix (e.g. 201234567A B12 , 201234567A 321 ), where a 3-character alphanumeric suffix can be added to your company's UEN to create multiple PayNow proxies. This is based off what proxy is registered with your bank and the respective bank account.Important:  Please  ensure that  your  bank  account  is  correctly  linked  with  the  PayNow  proxy  provided  to  avoid  payment errors. This can usually be done via the bank's iBanking website or mobile application. For clarifications on linking your PayNow proxy to your bank account, please contact your bank.



Page 30 from document Create_Update_Vendor_Record

## 2. View/ Update Vendor Record Details - Bank Details (PayNowBank DetailsPayment Method *Ihter-Bank GIROPayNowTelegraphic TranslerProxy Type *Proxy Value *--Plese Select Proxy Type--GST Registered *GST Registration Number *YesNoN.A.## PayNow  (PAYN) option selected.## Select your GST registration status.- If you are GST Registered, please select 'Yes' for GST Registered option. Then, enter your GST registration number (Please enter only the numbers and omit the ' -' dash).- If you are not GST Registered, please select 'No' for GST Registered option' .YourVendori



Page 31 from document Create_Update_Vendor_Record

## 2. View/ Update Vendor Record Details - Bank Details (TT)
IMAGE FOUND, DESCRIPTION : Bank Details section

Payment Method
- Options:
  - Inter-Bank GIRO
  - PayNow
  - Telegraphic Transfer (selected)

Bank details form (outlined orange box) with fields:
1) Country of Bank: Prefilled dropdown (example: - Singapore Bank Country -)
2) Bank Name: text input
3) Swift ID: text input
4) Account Number: text input
5) Bank Address: multi-line text input
6) Clearing Code: text input
7) Routing Code: text input
8) Payment Details: text input
9) Corresponding Bank Required: radio group
   - Yes
   - No (selected)

Layout/flow and relationships
- The selected payment method Telegraphic Transfer drives the visibility of the bank-details subform.
- Each field in the subform is a mandatory or optional entry (indicated by asterisk on the UI) to capture payment routing information.
- The “Corresponding Bank Required” option determines whether an additional bank is needed for the transfer.

Semantic keywords for indexing
- Bank Details, Telegraphic Transfer, SWIFT ID, Account Number, Bank Address, Clearing Code, Routing Code, Payment Details, Corresponding Bank Required, Yes/No, Country of Bank, Bank Name, Payment Method.
BankDetailsourVendor ID;PaymentMethodInter-BankGIROPayNowTelegraphicTransferCeuntry al DonkurkHomH!SaltID!Aarwunt Mumber O=ftn fesk Counry =Dank Adreu!Cearig Cod Okoutng Coie OPymm Deuh oComsponding Bank RaqyinidYisHo## Telegraphic Transfer (TT) option selected.Enter your TT bank details.The bank account provided must be registered under your entity's name with the bank.Please ensure to provide the correct bank details to avoid payment rejection by the bank. If you are unsure of your bank details, please contact your bank to confirm the information for your remittance transfer.



Page 32 from document Create_Update_Vendor_Record

## 2. View/ Update Vendor Record Details - Bank Details (TT)
IMAGE FOUND, DESCRIPTION : Semantic text extraction for database serialization

Section: Bank Details
- Payment Method options (single-select):
  - Inter-Bank GIRO
  - PayNow
  - Telegrahic Transfer (selected)
- Selected payment method: Telegraphic Transfer (note: label appears as “Telegrahic Transfer” in the image with a highlighted selection box)

Input fields (grouped in a single form block, orange outline):
- Country of Bank: select dropdown → options not displayed
- Bank Name: text input
- Swift ID*: text input
- Account Number*: text input
- Bank Address*: text input
- Clearing Code*: text input
- Routing Code*: text input
- Payment Details: text input
- Corresponding Bank Required: radio group
  - Yes
  - No

Notes:
- Required fields indicated by asterisk (*) next to labels
- The entire bank details section is framed with an orange border, and the selected payment method is highlighted with an orange border around the option.
## Bank DetailsPayment Method +Inter-Bank GIROPayNowTelegraphic TransferCountry ofBankSwiftID"StexBankCoomryTankAddresgClearingCodePaymtntOetaisUpdate  of  Telegraphic  Transfer  (TT)  bank  details function  is  not  available  for  local/foreign  vendors who  are  transacting  as  an    individual.  To  update your  TT  bank  details,  please  lodge  a  helpdesk ticket.GST registration update is not available for vendors who have registered a TT bank account. To update your GST registration details, please lodge a helpdesk ticket  for assistance.## Telegraphic Transfer (TT) option selected.After updating the bank details, click 'Next' and on the  summary  page,  click 'Next' again  to  submit your vendor record request.You can only submit e-Invoices after your vendor record has been approved.NOTE



Page 33 from document Create_Update_Vendor_Record

## Note for Inter-Bank GIRO registration1. Vendors who are receiving payments through Inter-Bank GIRO must have a registered bank account listed in the Vendors@Gov approved banks.## Key points to note for the following banks:## POSB/DBS BankPOSB/ DBS Bank code: 7171- DBS Bank LtdIf there are 9 digits in your account number, the branch code is '081 -POSB'If there are 10 digits in your account number, the branch code is the first 3 digits of your account number. For example, if your account number is 0012345678, the branch code is '001'.## MaybankThere are two bank codes (7302 &amp; 9636) available for Maybank account, and you are required to contact your bank to confirm the correct bank details (E.g.: Bank and Branch code, Bank Account) before updating it at Vendors@Gov portal.- (a) 732- Maybank Singapore Limited- (b) 9636- Malayan Banking Berhad- (c) For Maybank account holders, please enter bank account format as X-XXX-XXXXXX.## OCBC BankOCBC Bank code: 7339- Oversea-Chinese Banking Corporation LtdThe first numbers of your OCBC account number are branch codes. Your OCBC account number should either be 10 digits or 12 digits.## HSBC BankThere are two bank codes (7232 &amp; 9548) available for HSBC bank account, , and you are required to contact your bank to confirm the correct bank details (E.g.: Bank and Branch code, Bank Account) before updating it at Vendors@Gov portal.- (a) 7232- The Hongkong &amp; Shanghai Banking Corporation Ltd- (b) 9548- HSBC Bank (Singapore) Limited (for retail account)



Page 34 from document Create_Update_Vendor_Record

## Why am I unable to update my vendor details?1. Update  of  vendor  details  will  not  be  available  between  0500hrs  to  0600hrs,  and  1900hrs  to  1930hrs (GMT+8) from Monday to Saturday for routine system maintenance.2. You will not be able to update your vendor record details if:3. ➢4. Your vendor record is currently inactive . If you would like to activate your vendor record, you may do so by clicking on the 'Reactivate' button upon successful login. After your vendor record is activated, you may update your vendor record details at the portal.- Your vendor record was created under a specific agency's SET ID (Eg: MOF10) . Vendors with vendor ID tagged to a specific agency business unit (Eg: MOF10) are unable to update their vendor record in Vendors@Gov. You are required to approach the liaison officer at your client agency to update your vendor details in the Government Financial System (NFS@Gov).- You are a foreign individual who do not have Singpass. Update of vendor record details is not available for foreign individual who do not have Singpass. You are required  to  approach  the  liaison  officer  at  your  client  agency  to  update  your  vendor  details  in  the Government Financial System (NFS@Gov).



Page 35 from document Create_Update_Vendor_Record

## vendors@gov## Vendor Record User GuidesSelect the topics below to learn more about:## 1. Create Vendor RecordNew vendors will be directed to 'Create New Vendor' page to create a vendor record.2. View/ Update Vendor Record Details## 2. View/ Update Vendor Record DetailsExisting vendor may navigate to 'Update Vendor Details' to  update your name, contact, GST registration and bank details.## 3. Vendor Record StatusVendor record status include Approved, Unapproved, Inactive.1. Create Vendor Record3. Vendor Record StatusGYD



Page 36 from document Create_Update_Vendor_Record

## 3. Vendor Record Status| Status     | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Approved   | Vendors will be able to submit e-Invoices to Government agencies in Vendors@Gov portal after their vendor record is approved.                                                                                                                                                                                                                                                                                                                                                          |
| Unapproved | Please ensure the following: 1. Your vendor record 'Name' and 'Bank details ' are updated correctly in Vendors@Gov. 2. You have selected the correct login option. For more information on how to login, please refer to ' Login and Registration User Guide ' .                                                                                                                                                                                                                       |
| Inactive   | Your vendor record will be inactivated if: 1. There was no activity for more than 2 years; or 2. There was a failed interbank GIRO (IBG) payment to your bank account; or 3. You or your client agency has requested for the vendor record inactivation. If you would like to activate your vendor record, you may do so by clicking on the 'Reactivate' button upon successful login. After your vendor record is activated, you may update your vendor record details in the portal. |



Page 37 from document Create_Update_Vendor_Record

## vendors@gov## - END -GYD


