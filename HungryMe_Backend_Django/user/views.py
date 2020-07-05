from django.contrib.auth import logout
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

#importing the Decorators
from rest_framework.decorators import api_view,permission_classes,authentication_classes

#importing permissions and authentication
from rest_framework.permissions import IsAuthenticated

#importing Serializer
from .serializer import RegisterSerializer
from.serializer import CustomTokenObtainPairSerializer,UserSerializer


#importing models
from .models import User


#Email
from django.core.mail import EmailMultiAlternatives,EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.cache import cache
from django.conf import settings
import random



#Login to the application
class Login(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    logout(request)
    return Response({"message":"user has been successfull logout"})


class UserCreation(APIView):

    def post(self,request):
        '''
        data = {
                    "full_name":"X Y Z",
                    "username":"xyz",
                    "password":"xyz",
                    "email":"xyz@gmail.com",
                    "phone":"1234567890",
                    "account_type":"User"
                }
        '''
        user_data = request.data
        serializer = RegisterSerializer(data=user_data)
        username = user_data.get('username')
        email = user_data.get('email')
        user = User.objects.filter(username=username).first()
        email_user  = User.objects.filter(email=email).first()
        try:
            if user is not None:
                raise Exception(username+" already exist, try with other username!")
            if email_user is not None:
                raise Exception(email+" already registered with us")

            if serializer.is_valid():
                instance = serializer.create(serializer.validated_data)

                if instance is None:
                    return Exception("Some Error Occurred Please contact Support team")

                user = User.objects.filter(id=instance.id).first()
                serilizer_context = {'request': request}
                serializer = UserSerializer(user,context=serilizer_context)

                return Response(serializer.data,status=201) #201 for new User creation
            else:
                raise Exception(serializer.error_messages)
        except Exception as e:
            return Response({"error":str(e)},status=400)  
        


class UserAction(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self,id):
        user = User.objects.filter(id=id).first()
        return user

    def get(self,request,id=None):
        user = self.get_object(id)
        if user is None:
            return Response({"error":"Given user_id - "+str(id)+" user object not found"},status=404)
        serilizer_context = {'request': request}
        serializer = UserSerializer(user,context=serilizer_context)
        return Response(serializer.data,status=200)

    def put(self,request,id=None):
        user = self.get_object(id)
        if user is None:
            return Response({"error":"Given user_id - "+str(id)+" user object not found"},status=404)
        serilizer_context = {'request': request}
        serializer = UserSerializer(user,data=request.data,partial=True,context=serilizer_context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=200)
        return Response(serializer.errors, status=400)

    def delete(self,request,id=None):
        user = self.get_object(id)
        if user is None:
            return Response({"error":"Given user_id - "+str(id)+" user object not found"},status=404)
        user.delete()
        return Response(status=200)



@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def setNewPassword(request):
    data = request.data
    user = request.user
    if user is not None:
        if user.check_password(data['password']):
            user.set_password(data['new_password'])
            #print(user.password)
            user.save()
            return Response(200)
        else:
            return Response({"error": "Wrong password, please try again"}, status=400)
    else:
        return Response({"error": "Something went wrong, please try again after sometime"}, status=404)


@api_view(['POST'])
@permission_classes([])
def sendForgotPasswordMail(request):

    email_id = request.data['mail']
    username = User.objects.get(email=email_id).username
    # print(email_id,username)
    if username is not None:
        try:
            secret_key = generate_secret_key()
            cache.set('reset_pwd_%s' % (username),secret_key ,
                      settings.USER_RESET_PASSWORD_LINK_TIMEOUT)
            print(cache.get('reset_pwd_%s' % (username)))
            link = r""+str(settings.USER_RESET_PASSWORD_LINK_HOST)+"changepassowrd/"+username+"/"+secret_key
            html_content = render_to_string('email.html',{"username":username,"link":link})
            text_content = strip_tags(html_content)
            email = EmailMultiAlternatives(
                'Famesta: Reset Password?',
                text_content,
                settings.EMAIL_HOST_USER,
                [email_id]
            )
            email.attach_alternative(html_content,'text/html')
            email.send()
            return Response({"msg":"Email has been successfully sent to given id with password reset details"},status=200)
        except Exception as e:
            str(e)
            return Response({"error":"Something went wrong, please try again after some time"},status=500)
    else:
        return Response({"error":"Your email is not registered with us."},status=403)


def generate_secret_key():
    secret_key = ""
    small_char = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
    number = ['0','1','2','3','4','5','6','7','8','9']
    for i in range(0,20):
        secret_key += number[random.randrange(0,10,1)]
        secret_key += small_char[random.randrange(0,25,1)]
        secret_key += small_char[random.randrange(0, 25, 1)].upper()
    return secret_key


@api_view(['POST'])
@permission_classes([])
def verifyMailSecretKey(request):

    username = request.data['username']
    secret_key = request.data['secretkey']
    backend_secretkey = cache.get('reset_pwd_%s' % (username))
    # print(username)
    # print(backend_secretkey,secret_key)
    if backend_secretkey:
        if secret_key == backend_secretkey:
            return Response({"msg":"Your secret key has been successfully verified"},status=200)
        else:
            return Response({"error":"Your not authorized to use this link"},status=403)
    else:
        return Response({"error":"Your password link has been expired, please try again"},status=403)

@api_view(['PUT'])
@permission_classes([])
def setForgotPasswordWithNewPassword(request):
    data = request.data
    # print(data)
    user = User.objects.get(username=data['username'])
    secret_key = request.data['secretkey']
    backend_secretkey = cache.get('reset_pwd_%s' % (data['username']))
    if backend_secretkey:
        if backend_secretkey == secret_key:
            if user:
                user.set_password(data['password'])
                # print(user.password)
                user.save()
                #setting other value for cache only for 1 second
                cache.set('reset_pwd_%s' % (data['username'])," ",1)
                return Response({"msg":"Your password has been successfully changed"},status=200)
            else:
                return Response({"error":"Username does not exist on our system"},status=403)
        else:
            return Response({"error": "Your not authorized to use this link"}, status=403)
    else:
        return Response({"error": "Your password link has been expired, please try again"}, status=403)
    return Response({"msg":"successfully executed view"})


@api_view(['POST'])
@permission_classes([])
def sendContactMail(request):
    try:
        email_id = request.data['email']
        msg = request.data['msg']
        name = request.data['name']

        body = '''Hi SupportTeam,\n\n\n
                  '''+name+''' has contacted regarding below message\n\n\n
                  '''+msg+'''\n\n\n
                  for reference emailID - '''+email_id+'''
        '''
        email = EmailMessage("Contact Support Team :"+name+" | Email "+email_id,body,settings.EMAIL_HOST_USER,[settings.EMAIL_HOST_USER])
        email.send()
        return Response(200)
    except Exception as e:
        str(e)
        return Response(500)










