
def create_error_response(code=500, message="An error occurred"):
    return {
        "success": False,
        "code": code,
        "message": message,
        "data": None,
    }

def create_success_response(data=None, code=200, message="Success"):
    return {
        "success": True,
        "code": code,
        "message": message,
        "data": data,
    }
    


    