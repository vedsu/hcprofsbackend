from app import mongo

class Newsletter():

    # this is for masterdatabackend
    @staticmethod
    def count_newsletter():
        return list(mongo.db.newsletter_data.find({}))
    
    # this is for masterdatabackend
    @staticmethod
    def list_newsletter():
        newsletter_list = []
        try:
            newsletter_data = list(mongo.db.newsletter_data.find({}).sort({"topic":1}))
            for newsletter in newsletter_data:
                newsletter_dict ={
                    "id":newsletter.get("id"),
                    "topic":newsletter.get("topic"),
                    "category":newsletter.get("category"),
                    "description":newsletter.get("description"),
                    "website":newsletter.get("website"),
                    "price":newsletter.get("price"),
                    "thumbnail":newsletter.get("thumbnail"),
                    "document":newsletter.get("document"),

                }
                newsletter_list.append(newsletter_dict)
        except Exception as e:
            newsletter_list = [str(e)]
        return newsletter_list
    
    
    #this is for masterbackend
    @staticmethod
    def create_newsletter(newsletter):
        try:
            mongo.db.newsletter_data.insert_one(newsletter)
            return {"success":True, "message": "newsletter added successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    
    
    
    # this is for hcprofsbackend
    @staticmethod
    def activelist_newsletter():
        newsletter_list = []
        try:
            newsletter_data = list(mongo.db.newsletter_data.find({"status":"Active"}).sort({"topic":1}))
            for newsletter in newsletter_data:
                newsletter_dict ={
                    "id":newsletter.get("id"),
                    "topic":newsletter.get("topic"),
                    "category":newsletter.get("category"),
                    "description":newsletter.get("description"),
                    "website":newsletter.get("website"),
                    "price":newsletter.get("price"),
                    "thumbnail":newsletter.get("thumbnail"),
                    "document":newsletter.get("document"),

                }
                newsletter_list.append(newsletter_dict)
        except Exception as e:
            newsletter_list = [str(e)]
        return newsletter_list
        

    @staticmethod
    def edit_newsletter(n_id,newsletter_status):
        try:
            mongo.db.newsletter_data.update_one({"n_id":n_id},{"$set": {"status": newsletter_status}})
            return {"success":True, "message":"status update successfull"}
        
        except Exception as e:
            return {"success": False, "message": str(e)}