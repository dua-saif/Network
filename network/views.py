from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
from .models import User, Post, Follow, Like
import json

def remove_like(request, post_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    try:
        post = Post.objects.get(pk=post_id)
        user = request.user
        like = Like.objects.filter(user=user, post=post)
        like.delete()
        return JsonResponse({"message": "Like removed!"})
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def add_like(request, post_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    try:
        post = Post.objects.get(pk=post_id)
        user = request.user
        if Like.objects.filter(user=user, post=post).exists():
            return JsonResponse({"message": "Already liked."})
        newLike = Like(user=user, post=post)
        newLike.save()
        return JsonResponse({"message": "Like added!"})
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def edit(request, post_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            edit_post = Post.objects.get(pk=post_id)
            if edit_post.user != request.user:
                return JsonResponse({"error": "Unauthorized"}, status=403)
            edit_post.content = data["content"]
            edit_post.save()
            return JsonResponse({"message": "Change successful", "data": data["content"]})
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "POST request required."}, status=400)

def index(request):
    allPosts = Post.objects.all().order_by("-id")

    paginator = Paginator(allPosts, 10)
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)

    whoYouLiked = []
    if request.user.is_authenticated:
        whoYouLiked = list(
            Like.objects.filter(user=request.user).values_list('post_id', flat=True)
        )

    # 👇 Like counts per post ID
    like_counts = {
        post.id: Like.objects.filter(post=post).count()
        for post in posts_of_the_page
    }

    return render(request, "network/index.html", {
        "posts_of_the_page": posts_of_the_page,
        "whoYouLiked": json.dumps(whoYouLiked),
        "like_counts": like_counts  # 👈 new context
    })

def newPost(request):
    if request.method == "POST":
        content = request.POST.get('content', '').strip()
        if not content:
            return HttpResponseRedirect(reverse("index"))
        user = request.user
        post = Post(content=content, user=user)
        post.save()
        return HttpResponseRedirect(reverse("index"))
    else:
        return HttpResponseRedirect(reverse("index"))

def profile(request, user_id):
    user = User.objects.get(pk=user_id)
    allPosts = Post.objects.filter(user=user).order_by("-id")
    following = Follow.objects.filter(user=user)
    followers = Follow.objects.filter(user_follower=user)

    isFollowing = False
    if request.user.is_authenticated:
        isFollowing = Follow.objects.filter(user=request.user, user_follower=user).exists()

    paginator = Paginator(allPosts, 10)
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)

    whoYouLiked = []
    if request.user.is_authenticated:
        whoYouLiked = list(
            Like.objects.filter(user=request.user).values_list('post_id', flat=True)
        )

    return render(request, "network/profile.html", {
        "posts_of_the_page": posts_of_the_page,
        "username": user.username,
        "following": following,
        "followers": followers,
        "isFollowing": isFollowing,
        "user_profile": user,
        "whoYouLiked_json": json.dumps(whoYouLiked)
    })

def following(request):
    currentUser = request.user
    followingPeople = Follow.objects.filter(user=currentUser).values_list('user_follower', flat=True)
    followingPosts = Post.objects.filter(user__in=followingPeople).order_by("-id")

    paginator = Paginator(followingPosts, 10)
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)

    whoYouLiked = []
    if request.user.is_authenticated:
        whoYouLiked = list(
            Like.objects.filter(user=request.user).values_list('post_id', flat=True)
        )

    return render(request, "network/following.html", {
        "posts_of_the_page": posts_of_the_page,
        "whoYouLiked": json.dumps(whoYouLiked)
    })

def follow(request):
    if request.method == "POST":
        userfollow = request.POST.get("userfollow")
        currentUser = request.user
        try:
            userfollowData = User.objects.get(username=userfollow)
            if not Follow.objects.filter(user=currentUser, user_follower=userfollowData).exists():
                f = Follow(user=currentUser, user_follower=userfollowData)
                f.save()
            user_id = userfollowData.id
            return HttpResponseRedirect(reverse("profile", kwargs={'user_id': user_id}))
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse("index"))
    return HttpResponseRedirect(reverse("index"))

def unfollow(request):
    if request.method == "POST":
        userfollow = request.POST.get("userfollow")
        currentUser = request.user
        try:
            userfollowData = User.objects.get(username=userfollow)
            f = Follow.objects.get(user=currentUser, user_follower=userfollowData)
            f.delete()
            user_id = userfollowData.id
            return HttpResponseRedirect(reverse("profile", kwargs={'user_id': user_id}))
        except (User.DoesNotExist, Follow.DoesNotExist):
            return HttpResponseRedirect(reverse("index"))
    return HttpResponseRedirect(reverse("index"))

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirmation = request.POST.get("confirmation")

        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })

        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
