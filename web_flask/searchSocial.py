import os

import requests


class SocialModel:
    def __init__(self, username, email=None):
        self.username = username
        self.email = email

    def search_on_social_media(self):
        results = {
            'facebook': self.search_facebook(),
            'twitter': self.search_twitter(),
            'tiktok': self.search_tiktok(),
            'snapchat': self.search_snapchat(),
            'linkedin': self.search_linkedin(),
        }
        return results

    def search_facebook(self):
        # Use Facebook Graph API
        # You will need to create a Facebook App and get an access token
        access_token = 'YOUR_FACEBOOK_ACCESS_TOKEN'
        url = f"https://graph.facebook.com/v12.0/me?fields=id,name,posts.limit(1),likes.summary(true)&access_token={access_token}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                profile = {
                    "id": data["id"],
                    "full_name": data["name"],
                    "posts": data["posts"]["data"][0] if "posts" in data else "No posts available",
                    "total_likes": data["likes"]["summary"]["total_count"] if "likes" in data else "No likes data",
                }
                return profile
            else:
                return f"Error fetching data from Facebook: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"

    def search_twitter(self):
        # Twitter API (You need to sign up for a Twitter Developer account)
        # Use the Bearer Token for authentication
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

        if not bearer_token:
            return "Twitter token is missing."

        username = self.username.replace(" ", "")  # Ensure no spaces for Twitter usernames
        url = f"https://api.twitter.com/2/users/by/username/{username}?user.fields=public_metrics"
        url2 = f"https://api.x.com/2/users/by?usernames={username},twitterapi,adsapi&user.fields=created_at&expansions=pinned_tweet_id&tweet.fields=author_id,created_at"
        headers = {"Authorization": f"Bearer {bearer_token}"}

        try:
            response = requests.get(url, headers=headers)
            resp = requests.get(url2, headers=headers)
            if response.status_code == 200 and resp.status_code == 200:
                data = response.json()
                user_data = resp.json()
                print(data)
                print(user_data)
                profile = {
                    "Rate-limit": response.headers.get('x-rate-limit-reset'),
                    "id": data["data"]["id"],
                    "username": data["data"]["username"],
                    "full_name": data["data"]["name"],
                    "total_tweets": data["data"]["public_metrics"]["tweet_count"],
                    "last_tweet": "N/A"  # You would need another API call to get the actual last tweet
                }

                return profile, user_data

            else:
                return f"Error fetching data from Twitter: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"

    def search_tiktok(self):
        # TikTok does not have a public API for user data access directly.
        # You would need to use TikTok's business API or a scraping method for now.
        return "TikTok API integration is not publicly available."

    def search_snapchat(self):
        # Snapchat API requires OAuth, and it's mostly focused on ads and business data.
        # User data retrieval is limited and requires permissions.
        return "Snapchat API for public user data is not available."

    def search_linkedin(self):
        # LinkedIn API (You need to sign up for LinkedIn's Developer program)
        # Requires OAuth 2.0 authentication
        access_token = 'YOUR_LINKEDIN_ACCESS_TOKEN'
        url = "https://api.linkedin.com/v2/me"

        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                profile = {
                    "id": data["id"],
                    "full_name": data["localizedFirstName"] + " " + data["localizedLastName"],
                    "headline": data["headline"],
                    "last_activity": "N/A"  # Need to call activity endpoints for more details
                }
                return profile
            else:
                return f"Error fetching data from LinkedIn: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
