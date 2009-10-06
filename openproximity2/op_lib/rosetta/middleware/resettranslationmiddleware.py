
   
class ResetTranslationMiddleware(object):
   def process_request(self, request):
       
       from django.utils.translation import trans_real
       from django.utils.thread_support import currentThread
       
       trans_real._translations = {}
       trans_real._default = None
       #trans_real._accepted = {}
       trans_real._active.pop(currentThread(), None)

       
       