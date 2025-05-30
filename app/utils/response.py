
def create_error_response(code=500, message="An error occurred"):
    return {
        "data": None,
        "code": code,
        "success": False,
        "message": message
    }

def create_success_response(data=None, code=200, message="Success"):
    return {
        "data": data,
        "code": code,
        "success": True,
        "message": message
    }
    


    