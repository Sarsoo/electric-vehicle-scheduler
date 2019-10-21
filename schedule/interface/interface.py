

def get_status_dict(error: bool = False,
                    success: bool = False,
                    prohibited: bool = False):
    if error:
        return {'status': 'error'}
    elif success:
        return {'status': 'success'}
    elif prohibited:
        return {'status': 'prohibited'}
    raise ValueError('no status specified')


def create_response(response: dict,
                    error: bool = False,
                    success: bool = False,
                    prohibited: bool = False):

    complete_response = dict()

    status = get_status_dict(error=error, success=success, prohibited=prohibited)

    complete_response.update(response)
    complete_response.update(status)
    
    return complete_response
