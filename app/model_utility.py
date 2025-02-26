# Utilities
from app import mongo, mail, s3_client
from datetime import datetime, timedelta
import pytz
# from app import mail
from flask import render_template_string
from flask_mail import Message
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from io import BytesIO


class Utility():
    
    @staticmethod
    def view_coupon():
        coupon_list = [] 
        try:
            coupon_data = list(mongo.db.coupon_data.find({}))
            for coupon in coupon_data:
                
                    coupon_dict = {
                    "id": coupon.get("id"),
                    "coupon": coupon.get("coupon"),
                    "type": coupon.get("type"),
                    "amount": coupon.get("amount"),
                    "status": coupon.get("status")
                    }
                    coupon_list.append(coupon_dict)
        except Exception as e:
            coupon_list = {"error": str(e)}           
        
        return coupon_list
    
    
    @staticmethod
    def update_live_status():
        # Get current time in EST
        est = pytz.timezone('US/Eastern')
        current_time_est = datetime.now(est)
        try:
    
            # Update documents where the current time in EST is greater than the date_time and live is still true
            result = mongo.db.webinar_data.update_many(
                {
                    "date_time": {"$lt": current_time_est},
                    "sessionLive": True
                },
                {"$set": {"sessionLive": False}}
            )
            return {"success":True, "message":"live session updated"}
        
        except Exception as e:
            return {"success":False, "message":str(e)}

    @staticmethod
    def generate_pdf(Webinar, customername, country, websiteUrl, billingemail, date_time_str, orderamount, invoice_number, discount, zip_code, orderID):
        def wrap_text(text, max_chars_per_line):
            words = text.split()
            lines = []
            current_line = ""
            
            for word in words:
                if len(current_line) + len(word) + 1 <= max_chars_per_line:
                    current_line += " " + word if current_line else word
                else:
                    lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            return lines
        documentTitle = "HCProfs"
        title = "Invoice Details"
    
        leftSection = [
        f'Invoice Number # {invoice_number}',
        f'Date : {date_time_str}',
        ]
    
        rightSection1 = [
        f'cs@hcprofs.com',
        f'https://hcprofs.com/'
        ]
    
        customerDetails = [
        'Recipient Details:',
        f'Name : {customername}',
        f'Email : {customeremail}',
        f'Country : {country}'
        f'Zip Code : {zip_code}'
        ]
    
        orderDetails = [
        f'#: {orderID}'
        ]
    
        webinarDetails = [
        'Description'
        ]
        max_chars_per_line = 60
        wrapped_webinar_details = wrap_text(Webinar, max_chars_per_line)
        
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        pdf.rect(20, 20, width - 40, height - 40, stroke=1, fill=0)
        pdf.setFont("Helvetica-Bold", 79)
        pdf.setFillColorRGB(0.9, 0.9, 0.9)
        pdf.saveState()
        pdf.translate(width / 2, height / 2)
        pdf.rotate(45)
        pdf.drawCentredString(0, 0, "HCProfs")
        pdf.restoreState()
        pdf.setFillColor(colors.black)

        y_shift = 50

        pdf.setFont('Helvetica-Bold', 17)
        pdf.drawCentredString(width / 2, height - 40 - y_shift, documentTitle)
        pdf.setFont('Helvetica-Bold', 15)
        pdf.drawCentredString(width / 2, height - 75 - y_shift, title)

        pdf.setFont("Helvetica-Bold", 11)
        text = pdf.beginText(40, height - 105 - y_shift)
        for line in leftSection:
            text.textLine(line)
        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 105 - y_shift)
        for line in rightSection1:
            text.textLine(line)
        pdf.drawText(text)

        pdf.line(40, height - 170 - y_shift, width - 40, height - 170 - y_shift)

        text = pdf.beginText(40, height - 190 - y_shift)
        text.setFont("Helvetica-Bold", 13)
        text.textLine(customerDetails[0])
        text.setFont("Helvetica", 11)
        text.moveCursor(0, 18)
        for line in customerDetails[1:]:
            text.textLine(line)
        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 190 - y_shift)
        for line in orderDetails:
            text.textLine(line)
        pdf.drawText(text)

        
        pdf.line(40, height - 320 - y_shift, width - 40, height - 320 - y_shift)

        text = pdf.beginText(40, height - 340 - y_shift)
        text.setFont("Helvetica-Bold", 11)
        text.textLine(webinarDetails[0])
        for line in wrapped_webinar_details:
            text.textLine(line)
        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 340 - y_shift)
        text.setFont("Helvetica-Bold", 11)
        text.textLine('Total Price')
        text.textLine(f'${orderamount + discount}')
        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 420 - y_shift)
        text.setFont("Helvetica-Bold", 11)
        text.textLine(f'Subtotal: ${orderamount + discount}')
        text.textLine(f'Discount: -${discount}')
        text.textLine(f'Grand Total: ${orderamount}')
        pdf.drawText(text)

        thankYouNote = 'Thank you for your Purchase'
        queryNote = 'Query? Reach out to us at cs@hcprofs.com !'
        signature = 'Webinar Organizer Team'
        pdf.setFont("Helvetica-Oblique", 11)
        pdf.setFillColor(colors.black)
        pdf.drawCentredString(width / 2, 125, thankYouNote)
        pdf.drawCentredString(width / 2, 105, queryNote)
        pdf.drawCentredString(width / 2, 85, signature)
        
        pdf.setFont("Helvetica", 11)
        pdf.drawCentredString(width / 2, 65, f'Website - {websiteUrl}')
        
        pdf.save()
        buffer.seek(0)

        # Upload the PDF to S3
        bucket_name = "webinarprofs"
        object_key = f'websiteorderist/{invoice_number}.pdf'
        s3_client.put_object(
            Body=buffer,
            Bucket=bucket_name,
            Key=object_key
        )

        # Generate S3 URL
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"
        return s3_url
    
    @staticmethod
    def generatelocal_pdf(Webinar, customername, country, websiteUrl, billingemail, date_time_str, orderamount, invoice_number, discount, zip_code, orderID):
        def wrap_text(text, max_chars_per_line):
            words = text.split()
            lines = []
            current_line = ""
            
            for word in words:
                if len(current_line) + len(word) + 1 <= max_chars_per_line:
                    current_line += " " + word if current_line else word
                else:
                    lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            return lines
        documentTitle = "HCProfs"
        title = "Invoice Details"
    
        leftSection = [
        f'Invoice Number # {invoice_number}',
        f'Date : {date_time_str}',
        ]
    
        rightSection1 = [
        f'cs@hcprofs.com',
        f'https://hcprofs.com/'
        ]
    
        customerDetails = [
        'Recipient Details:',
        f'Name : {customername}',
        f'Email : {customeremail}',
        f'Country : {country}'
        f'Zip Code : {zip_code}'
        ]
    
        orderDetails = [
        f'#: {orderID}'
        ]
    
        webinarDetails = [
        'Description'
        ]
        max_chars_per_line = 60
        wrapped_webinar_details = wrap_text(Webinar, max_chars_per_line)
        
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        pdf.rect(20, 20, width - 40, height - 40, stroke=1, fill=0)
        pdf.setFont("Helvetica-Bold", 79)
        pdf.setFillColorRGB(0.9, 0.9, 0.9)
        pdf.saveState()
        pdf.translate(width / 2, height / 2)
        pdf.rotate(45)
        pdf.drawCentredString(0, 0, "HCProfs")
        pdf.restoreState()
        pdf.setFillColor(colors.black)

        y_shift = 50

        pdf.setFont('Helvetica-Bold', 17)
        pdf.drawCentredString(width / 2, height - 40 - y_shift, documentTitle)
        pdf.setFont('Helvetica-Bold', 15)
        pdf.drawCentredString(width / 2, height - 75 - y_shift, title)

        pdf.setFont("Helvetica-Bold", 11)
        text = pdf.beginText(40, height - 105 - y_shift)
        for line in leftSection:
            text.textLine(line)
        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 105 - y_shift)
        for line in rightSection1:
            text.textLine(line)
        pdf.drawText(text)

        pdf.line(40, height - 170 - y_shift, width - 40, height - 170 - y_shift)

        text = pdf.beginText(40, height - 190 - y_shift)
        text.setFont("Helvetica-Bold", 13)
        text.textLine(customerDetails[0])
        text.setFont("Helvetica", 11)
        text.moveCursor(0, 18)
        for line in customerDetails[1:]:
            text.textLine(line)
        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 190 - y_shift)
        for line in orderDetails:
            text.textLine(line)
        pdf.drawText(text)

        
        pdf.line(40, height - 320 - y_shift, width - 40, height - 320 - y_shift)

        text = pdf.beginText(40, height - 340 - y_shift)
        text.setFont("Helvetica-Bold", 11)
        text.textLine(webinarDetails[0])
        for line in wrapped_webinar_details:
            text.textLine(line)
        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 340 - y_shift)
        text.setFont("Helvetica-Bold", 11)
        text.textLine('Total Price')
        text.textLine(f'${orderamount + discount}')
        pdf.drawText(text)

        text = pdf.beginText(width - 180, height - 420 - y_shift)
        text.setFont("Helvetica-Bold", 11)
        text.textLine(f'Subtotal: ${orderamount + discount}')
        text.textLine(f'Discount: -${discount}')
        text.textLine(f'Grand Total: ${orderamount}')
        pdf.drawText(text)

        thankYouNote = 'Thank you for your Purchase'
        queryNote = 'Query? Reach out to us at cs@hcprofs.com !'
        signature = 'Webinar Organizer Team'
        pdf.setFont("Helvetica-Oblique", 11)
        pdf.setFillColor(colors.black)
        pdf.drawCentredString(width / 2, 125, thankYouNote)
        pdf.drawCentredString(width / 2, 105, queryNote)
        pdf.drawCentredString(width / 2, 85, signature)
        
        pdf.setFont("Helvetica", 11)
        pdf.drawCentredString(width / 2, 65, f'Website - {websiteUrl}')
        
        pdf.save()
        buffer.seek(0)

        # Upload the PDF to S3
        bucket_name = "webinarprofs"
        object_key = f'websiteorder/{invoice_number}.pdf'
        s3_client.put_object(
            Body=buffer,
            Bucket=bucket_name,
            Key=object_key
        )

        # Generate S3 URL
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"
        return s3_url

        
    

    





    # @staticmethod
    # def generatelocal_pdf(Webinar,customername, country, websiteUrl, customeremail, date_time_str, orderamount, invoice_number):
    #     # File and document details
    #     # documentTitle = 'Payment Receipt'
    #     # title = 'Invoice Details'
        
    #     # # Sections of the Invoice
    #     # leftSection = [
    #     #     f'Invoice Number - {invoice_number}',
    #     #     f'Order Date - {date_time_str}'
    #     # ]
    #     # rightSection = [
    #     #     f'Order Amount - ${orderamount}'
    #     # ]
    #     # customerDetails = [
    #     #     'Customer Details:',
    #     #     f'Customer Name -  {customername}',
    #     #     f'Registered Email - {customeremail}',
    #     #     f'Country - {country}',
    #     #     # f'Webinar Date: {webinardate}',
    #     #     # f'Webinar Session: {comma_separated_keys}'
    #     # ]
    #     # webinarDetails = [
    #     #     'Webinar Name -',
    #     #     f'{Webinar}'  # Line break handled by keeping as separate lines
    #     # ]
    #     # thankYouNote = 'query?reach out to us at cs@hcprofs.com !'
    #     # signature = 'Webinar Organizer Team'

    #     # # Create PDF in memory
    #     # buffer = BytesIO()
    #     # pdf = canvas.Canvas(buffer, pagesize=letter)
    #     # width, height = letter

    #     # # Set the title of the document
    #     # pdf.setTitle(documentTitle)

    #     # # Add border around the page
    #     # pdf.rect(20, 20, width - 40, height - 40, stroke=1, fill=0)

    #     # # Shift all content downward
    #     # y_shift = 40  # Shift content down by 40 units

    #     # # Document Title at the top
    #     # pdf.setFont('Helvetica-Bold', 18)
    #     # pdf.drawCentredString(width / 2, height - 40 - y_shift, documentTitle)

    #     # # Create the title by setting its font and putting it on the canvas
    #     # pdf.setFont('Helvetica-Bold', 14)
    #     # pdf.drawCentredString(width / 2, height - 80 - y_shift, title)

    #     # # First section - Invoice details
    #     # pdf.setFont("Helvetica-Bold", 10)
    #     # text = pdf.beginText(40, height - 120 - y_shift)
    #     # for line in leftSection:
    #     #     text.textLine(line)
    #     # pdf.drawText(text)

    #     # text = pdf.beginText(width - 250, height - 120 - y_shift)
    #     # for line in rightSection:
    #     #     text.textLine(line)
    #     # pdf.drawText(text)

    #     # # Line separator for the second section
    #     # pdf.line(40, height - 160 - y_shift, width - 40, height - 160 - y_shift)

    #     # # Second section - Customer details
    #     # text = pdf.beginText(40, height - 180 - y_shift)
    #     # text.setFont("Helvetica-Bold", 10)
    #     # text.textLine(customerDetails[0])  # Customer Details heading
    #     # text.setFont("Helvetica", 14)  # Change font for the rest of the text
    #     # text.moveCursor(0, 20)  # Add space after the heading

    #     # for line in customerDetails[1:]:
    #     #     text.textLine(line)
    #     #     text.moveCursor(0, 15)  # Add space between lines to avoid overwriting
    #     # pdf.drawText(text)

    #     # # Line separator for the third section
    #     # pdf.line(40, height - 340 - y_shift, width - 40, height - 340 - y_shift)

    #     # # Third section - Webinar details
    #     # text = pdf.beginText(40, height - 360 - y_shift)
    #     # text.setFont("Helvetica-Bold", 10)
    #     # for line in webinarDetails:
    #     #     text.textLine(line)
    #     # pdf.drawText(text)

    #     # # Add the thank you note and signature at the bottom of the page
    #     # pdf.setFont("Helvetica-Oblique", 8)
    #     # pdf.setFillColor(colors.black)
    #     # pdf.drawCentredString(width / 2, 80, thankYouNote)
    #     # pdf.drawCentredString(width / 2, 60, signature)
        
    #     # # Add the website URL at the bottom-most position
    #     # pdf.setFont("Helvetica", 8)
    #     # pdf.drawCentredString(width / 2, 40, f'Website - {websiteUrl}')

    #     # # Save the PDF to the in-memory buffer
    #     # pdf.save()
    #     # buffer.seek(0)
    #     # Function to wrap text for long webinar descriptions
    #     def wrap_text(text, max_chars_per_line):
    #         words = text.split()
    #         lines = []
    #         current_line = ""
        
    #         for word in words:
    #             if len(current_line) + len(word) + 1 <= max_chars_per_line:
    #                 current_line += " " + word if current_line else word
    #             else:
    #                 lines.append(current_line)
    #                 current_line = word
        
    #         if current_line:
    #             lines.append(current_line)
        
    #         return lines
    #     documentTitle = "HCProfs"
    #     title = "Invoice Details"
        
    #     # Sections of the Invoice
    #     leftSection = [
    #         f'Invoice Number # {invoice_number}',
    #         f'Date : {date_time_str}',
          
    #     ]
        
    #     rightSection3 = [
    #         f'Grand Total : ${orderamount}'
    #     ]
        
    #     rightSection2 = [
    #         f'Total Price',
    #         f'${orderamount}'
    #     ]
        
    #     rightSection1 = [
    #         f'cs@hcprofs.com'
    #     ]
        
    #     customerDetails = [
    #         'Recipient Details:',
    #         f'Name : {customername}',
    #         f'Email : {customeremail}',
    #         f'Country : {country}'
    #     ]
        
    #     webinarDetails = [
    #         'Description',
           
    #     ]
    #     # Wrap webinar description text
    #     max_chars_per_line = 60  # Adjust as needed
    #     wrapped_webinar_details = wrap_text(Webinar, max_chars_per_line)
       
        
    #     # Create PDF in memory
    #     buffer = BytesIO()
    #     pdf = canvas.Canvas(buffer, pagesize=letter)
    #     width, height = letter
        
    #     # Add border around the page
    #     pdf.rect(20, 20, width - 40, height - 40, stroke=1, fill=0)
        
    #     # Add centered diagonal shadow text "HCProfs" in the background
    #     pdf.setFont("Helvetica-Bold", 80)
    #     pdf.setFillColorRGB(0.9, 0.9, 0.9)  # Light gray color for the shadow text
    #     pdf.saveState()
    #     pdf.translate(width / 2, height / 2)
    #     pdf.rotate(45)  # Rotate text diagonally at the center
    #     pdf.drawCentredString(0, 0, "HCProfs")
    #     pdf.restoreState()

        
    #     # Reset fill color for normal text
    #     pdf.setFillColor(colors.black)
        
    #     # Shift all content downward
    #     y_shift = 40  # Shift content down by 40 units
        
    #     # Document Title at the top
    #     pdf.setFont('Helvetica-Bold', 18)
    #     pdf.drawCentredString(width / 2, height - 40 - y_shift, documentTitle)
        
    #     # Create the title
    #     pdf.setFont('Helvetica-Bold', 16)
    #     pdf.drawCentredString(width / 2, height - 80 - y_shift, title)
        
    #     # First section - Invoice details
    #     pdf.setFont("Helvetica-Bold", 12)
    #     text = pdf.beginText(40, height - 120 - y_shift)
    #     for line in leftSection:
    #         text.textLine(line)
    #     pdf.drawText(text)
        
    #     text = pdf.beginText(width - 180, height - 120 - y_shift)
    #     text.setFont("Helvetica-Bold", 10)
    #     for line in rightSection1:
    #         text.textLine(line)
    #     pdf.drawText(text)
        
    #     # Line separator for the second section
    #     pdf.line(40, height - 180 - y_shift, width - 40, height - 180 - y_shift)
        
    #     # Second section - Customer details
    #     text = pdf.beginText(40, height - 200 - y_shift)
    #     text.setFont("Helvetica-Bold", 14)
    #     text.textLine(customerDetails[0])  # Customer Details heading
    #     text.setFont("Helvetica", 12)  # Change font for the rest of the text
    #     text.moveCursor(0, 20)  # Add space after the heading
        
    #     for line in customerDetails[1:]:
    #         text.textLine(line)
    #         text.moveCursor(0, 15)  # Add space between lines to avoid overwriting
    #     pdf.drawText(text)
        
    #     # Line separator for the third section
    #     pdf.line(40, height - 340 - y_shift, width - 40, height - 340 - y_shift)
        
    #     # Third section - Webinar details
    #     text = pdf.beginText(40, height - 360 - y_shift)
    #     text.setFont("Helvetica-Bold", 12)
    #     text.textLine(webinarDetails[0])  # Title

    #     for line in wrapped_webinar_details:
    #         text.textLine(line)
    #     pdf.drawText(text)
        
    #     text = pdf.beginText(width - 180, height - 360 - y_shift)
    #     text.setFont("Helvetica-Bold", 12)
    #     for line in rightSection2:
    #         text.textLine(line)
    #     pdf.drawText(text)
        
    #     text = pdf.beginText(width - 180, height - 460 - y_shift)
    #     text.setFont("Helvetica-Bold", 12)
    #     for line in rightSection3:
    #         text.textLine(line)
    #     pdf.drawText(text)
        
    #     # Add the thank you note and signature at the bottom of the page
    #     # pdf.setFont("Helvetica-Oblique", 12)
    #     # pdf.setFillColor(colors.black)
    #     # pdf.drawCentredString(width / 2, 120, thankYouNote)
    #     # pdf.drawCentredString(width / 2, 80, signature)

    #     # Add the thank you note and signature at the bottom of the page
    #     thankYouNote = 'Query? Reach out to us at cs@hcprofs.com !'
    #     signature = 'Webinar Organizer Team'
    #     pdf.setFont("Helvetica-Oblique", 12)
    #     pdf.setFillColor(colors.black)
    #     pdf.drawCentredString(width / 2, 120, thankYouNote)
    #     pdf.drawCentredString(width / 2, 80, signature)
        
    #     # Add the website URL at the bottom-most position
    #     pdf.setFont("Helvetica", 12)
    #     pdf.drawCentredString(width / 2, 60, f'Website - {websiteUrl}')
        
    #     # Save the PDF to the in-memory buffer
    #     pdf.save()
    #     buffer.seek(0)

    #     # Upload the PDF to S3
    #     bucket_name = "webinarprofs"
    #     object_key = f'websiteorderist/{invoice_number}.pdf'
    #     s3_client.put_object(
    #         Body=buffer,
    #         Bucket=bucket_name,
    #         Key=object_key
    #     )

    #     # Generate S3 URL
    #     s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"
    #     return s3_url
    
    # @staticmethod
    # def generate_pdf(Webinar,customername, country, websiteUrl, customeremail, date_time_str, orderamount, invoice_number):
    #     # File and document details
    #     documentTitle = 'Payment Receipt'
    #     title = 'Invoice Details'
        
    #     # Sections of the Invoice
    #     leftSection = [
    #         f'Invoice Number - {invoice_number}',
    #         f'Order Date - {date_time_str}'
    #     ]
    #     rightSection = [
    #         f'Order Amount - ${orderamount}'
    #     ]
    #     customerDetails = [
    #         'Customer Details:',
    #         f'Customer Name -  {customername}',
    #         f'Registered Email - {customeremail}',
    #         f'Country - {country}',
    #         # f'Webinar Date: {webinardate}',
    #         # f'Webinar Session: {comma_separated_keys}'
    #     ]
    #     webinarDetails = [
    #         'Webinar Name -',
    #         f'{Webinar}'  # Line break handled by keeping as separate lines
    #     ]
    #     thankYouNote = 'query?reach out to us at cs@hcprofs.com !'
    #     signature = 'Webinar Organizer Team'

    #     # Create PDF in memory
    #     buffer = BytesIO()
    #     pdf = canvas.Canvas(buffer, pagesize=letter)
    #     width, height = letter

    #     # Set the title of the document
    #     pdf.setTitle(documentTitle)

    #     # Add border around the page
    #     pdf.rect(20, 20, width - 40, height - 40, stroke=1, fill=0)

    #     # Shift all content downward
    #     y_shift = 40  # Shift content down by 40 units

    #     # Document Title at the top
    #     pdf.setFont('Helvetica-Bold', 18)
    #     pdf.drawCentredString(width / 2, height - 40 - y_shift, documentTitle)

    #     # Create the title by setting its font and putting it on the canvas
    #     pdf.setFont('Helvetica-Bold', 14)
    #     pdf.drawCentredString(width / 2, height - 80 - y_shift, title)

    #     # First section - Invoice details
    #     pdf.setFont("Helvetica-Bold", 10)
    #     text = pdf.beginText(40, height - 120 - y_shift)
    #     for line in leftSection:
    #         text.textLine(line)
    #     pdf.drawText(text)

    #     text = pdf.beginText(width - 250, height - 120 - y_shift)
    #     for line in rightSection:
    #         text.textLine(line)
    #     pdf.drawText(text)

    #     # Line separator for the second section
    #     pdf.line(40, height - 160 - y_shift, width - 40, height - 160 - y_shift)

    #     # Second section - Customer details
    #     text = pdf.beginText(40, height - 180 - y_shift)
    #     text.setFont("Helvetica-Bold", 10)
    #     text.textLine(customerDetails[0])  # Customer Details heading
    #     text.setFont("Helvetica", 14)  # Change font for the rest of the text
    #     text.moveCursor(0, 20)  # Add space after the heading

    #     for line in customerDetails[1:]:
    #         text.textLine(line)
    #         text.moveCursor(0, 15)  # Add space between lines to avoid overwriting
    #     pdf.drawText(text)

    #     # Line separator for the third section
    #     pdf.line(40, height - 340 - y_shift, width - 40, height - 340 - y_shift)

    #     # Third section - Webinar details
    #     text = pdf.beginText(40, height - 360 - y_shift)
    #     text.setFont("Helvetica-Bold", 10)
    #     for line in webinarDetails:
    #         text.textLine(line)
    #     pdf.drawText(text)

    #     # Add the thank you note and signature at the bottom of the page
    #     pdf.setFont("Helvetica-Oblique", 8)
    #     pdf.setFillColor(colors.black)
    #     pdf.drawCentredString(width / 2, 80, thankYouNote)
    #     pdf.drawCentredString(width / 2, 60, signature)
        
    #     # Add the website URL at the bottom-most position
    #     pdf.setFont("Helvetica", 8)
    #     pdf.drawCentredString(width / 2, 40, f'Website - {websiteUrl}')

    #     # Save the PDF to the in-memory buffer
    #     pdf.save()
    #     buffer.seek(0)

    #     # Upload the PDF to S3
    #     bucket_name = "webinarprofs"
    #     object_key = f'websiteorder/{invoice_number}.pdf'
    #     s3_client.put_object(
    #         Body=buffer,
    #         Bucket=bucket_name,
    #         Key=object_key
    #     )

    #     # Generate S3 URL
    #     s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"
    #     return s3_url
    
    @staticmethod
    def subscribe_list(subscriber_email, subscriber_name, subscription_type, subscriber_jobtitle):
       current_datetime = datetime.now()
       try:
            mongo.db.subscriber_list.insert_one({"email":subscriber_email, "name":subscriber_name,"jobtitle":subscriber_jobtitle,"subscription_type":subscription_type,"type":"subscriber", "date":current_datetime})
            return ({"success": True, "message": "subscribed successfully"}),201
       except Exception as e:
            return ({"success": False, "message": str(e)}), 403

    @staticmethod
    def unsubscribe_list(unsubscriber):
       current_datetime = datetime.now()
       try:
            mongo.db.subscriber_list.insert_one({"email":unsubscriber, "type":"unsubscriber", "date":current_datetime})
            return ({"success": True, "message": "unsubscribed successfully"}),201
       except Exception as e:
            return ({"success": False, "message": str(e)}), 403
       
    @staticmethod
    def forgotpassword(email, website = "HEALTHPROFS"):
        try:
            usercredentails =list(mongo.db.user_data.find({"$and":[{"email":email},{"website":website}]}))
            if usercredentails:
                try:
                    usercredentail = usercredentails[0]
                    email = usercredentail.get("email")
                    password = usercredentail.get("password")
                    websiteUrl = usercredentail.get("websiteUrl")
                    
                    msg = Message('Your Account Credentials', sender = 'cs@hcprofs.com', recipients = [email])
                    
                    msg.body = f"""
                                   Dear Customer,

                                   Welcome to our website!

                                   Here are your account credentials:

                                   Email: {email}
                                   Password: {password}
                                   Website: {websiteUrl}

                                   Please keep this information secure and do not share it with anyone.

                                   Thanks & Regards!
                                   Webinar Organizer Team
                                   
                                   """
                    msg.html = render_template_string("""
                                   <p>Dear Customer,</p>
                                   <p>Welcome to our website!</p>
                                   <p>Here are your account credentials:</p>
                                   <ul>
                                        <li><b>Email:</b> {{ email }}</li>
                                        <li><b>Password:</b> {{ password }}</li>
                                        <li><b>Website:</b> <a href="{{ website }}">{{ website }}</a></li>
                                   </ul>
                                   <p>Please keep this information secure and do not share it with anyone.</p>
                                   <p>Thanks & Regards!<br>Webinar Organizer Team</p>
                                   """, email=email, password=password, website=websiteUrl)
                    mail.send(msg)
                    return ({"success": True, "message": "email sent successfully"}),200
                
                except Exception as e:
                   return ({"success": False, "message": str(e)}), 403

            else:
               return ({"success": False, "message": "User doesnot exists"}), 200
        except Exception as e:
            return ({"success": False, "message": str(e)}), 403
        
         

      
