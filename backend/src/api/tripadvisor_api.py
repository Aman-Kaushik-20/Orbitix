import os
import asyncio
import httpx
from dotenv import load_dotenv
load_dotenv('backend/.env')

class TripAdvisorAPIClient:
    """
    An asynchronous client for interacting with the TripAdvisor API on RapidAPI.
    """

    def __init__(self):
        """
        Initializes the TripAdvisorAPIClient.

        Loads the API key from the .env file and sets up the request headers.
        Raises:
            ValueError: If the TRIPADVISOR_API_KEY is not found in the environment variables.
        """
        load_dotenv()
        self.api_key = os.getenv("TRIPADVISOR_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found. Please create a .env file and add TRIPADVISOR_API_KEY.")

        self.base_url = "https://tripadvisor16.p.rapidapi.com/api/v1"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "X-rapidapi-host": "tripadvisor16.p.rapidapi.com"
        }

    async def _make_request(self, method, endpoint, params=None):
        """
        Helper method to make asynchronous requests to the API.

        Args:
            method (str): HTTP method (e.g., 'GET').
            endpoint (str): API endpoint to call.
            params (dict, optional): Query parameters for the request. Defaults to None.

        Returns:
            dict: The JSON response from the API.
        """
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, headers=self.headers, params=params, timeout=30.0)
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                return response.json()
            except httpx.HTTPStatusError as http_err:
                print(f"HTTP error occurred: {http_err}")
            except httpx.RequestError as req_err:
                print(f"Request error occurred: {req_err}")
            except KeyError as key_err:
                print(f"Key error in JSON response: {key_err}")
            return None

    async def search_hotels_by_city(self, city_name, currency="USD"):
        """
        Searches for hotels in a given city asynchronously.

        Args:
            city_name (str): The name of the city to search for hotels in.
            currency (str, optional): The currency for pricing. Defaults to "USD".

        Returns:
            list: A list of hotels found in the specified city.
        """
        # 1. Get location ID for the city
        location_data = await self._make_request("GET", "/hotels/searchLocation", params={"query": city_name})
        if not location_data or "data" not in location_data or not location_data["data"]:
            return []
        '''
        {
  "status": true,
  "message": "Success",
  "timestamp": 1661590930510,
  "data": [
    {
      "title": "<b>New Delhi</b>",
      "documentId": "304551",
      "trackingItems": "geo",
      "secondaryText": "National Capital Territory of Delhi, India"
    },
    {
      "title": "<b>New York City</b>",
      "documentId": "60763",
      "trackingItems": "geo",
      "secondaryText": "New York, United States"
    },
    {
      "title": "<b>Newark</b>",
      "documentId": "46671",
      "trackingItems": "geo",
      "secondaryText": "New Jersey, United States"
    },
    {
      "title": "<b>New Orleans</b>",
      "documentId": "60864",
      "trackingItems": "geo",
      "secondaryText": "Louisiana, United States"
    },
    {
      "title": "<b>New Zealand</b>",
      "documentId": "255104",
      "trackingItems": "geo",
      "secondaryText": "South Pacific"
    },
    {
      "title": "<b>New Tehri</b>",
      "documentId": "1131922",
      "trackingItems": "geo",
      "secondaryText": "Uttarakhand, India"
    },
    {
      "title": "<b>New Admar Guest House</b>",
      "documentId": "4077130",
      "trackingItems": "hotel",
      "secondaryText": "Udupi, India",
      "image": {
        "__typename": "AppPresentation_PhotoItemSizeDynamic",
        "maxHeight": 2250,
        "maxWidth": 4000,
        "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/19/82/17/71/new-admar-guest-house.jpg?w={width}&h={height}&s=1"
      }
    },
    {
      "title": "<b>New Jacquline Heritage Houseboats Nigeen Lake</b>",
      "documentId": "2534693",
      "trackingItems": "hotel",
      "secondaryText": "Srinagar, Kashmir, India",
      "image": {
        "__typename": "AppPresentation_PhotoItemSizeDynamic",
        "maxHeight": 3040,
        "maxWidth": 4056,
        "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/15/b2/77/8a/exterior.jpg?w={width}&h={height}&s=1"
      }
    },
    {
      "title": "<b>New Cottage</b>",
      "documentId": "7891511",
      "trackingItems": "hotel",
      "secondaryText": "Nathdwara, India",
      "image": {
        "__typename": "AppPresentation_PhotoItemSizeDynamic",
        "maxHeight": 701,
        "maxWidth": 667,
        "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/18/fb/24/ac/new-cottage.jpg?w={width}&h={height}&s=1"
      }
    }
  ]
}
        '''
        try:
            geoId = location_data["data"][0]["geoId"]
        except (KeyError, IndexError):
            print(f"Could not find locationId for city: {city_name}")
            return []

        # 2. Search for hotels using the location ID
        hotel_data = await self._make_request("GET", "/hotels/searchHotels", params={"geoId": geoId, "checkIn":"2025-08-11", "checkOut":"2025-08-15", "currency": currency})
        '''
        {
  "status": true,
  "message": "Success",
  "timestamp": 1661591870938,
  "data": {
    "sortDisclaimer": "2,000 of 2,000+ places are available, sorted by <span class=\"underline\">best value</span>",
    "data": [
      {
        "id": "5408488",
        "title": "1. Abode Bombay",
        "primaryInfo": "Free breakfast included",
        "secondaryInfo": "Wellington Pier",
        "badge": {},
        "bubbleRating": {
          "count": "1,037",
          "rating": 4.5
        },
        "isSponsored": false,
        "accentedLabel": false,
        "provider": "Booking.com",
        "priceForDisplay": null,
        "strikethroughPrice": null,
        "priceDetails": null,
        "priceSummary": null,
        "cardPhotos": [
          {
            "__typename": "AppPresentation_PhotoItem",
            "sizes": {
              "__typename": "AppPresentation_PhotoItemSizeDynamic",
              "maxHeight": 1733,
              "maxWidth": 2600,
              "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0e/e5/ee/a4/superior-luxury-room--v15259560.jpg?w={width}&h={height}&s=1"
            }
          },
          {
            "__typename": "AppPresentation_PhotoItem",
            "sizes": {
              "__typename": "AppPresentation_PhotoItemSizeDynamic",
              "maxHeight": 886,
              "maxWidth": 1737,
              "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/05/4c/29/80/bedroom.jpg?w={width}&h={height}&s=1"
            }
          },
          {
            "__typename": "AppPresentation_PhotoItem",
            "sizes": {
              "__typename": "AppPresentation_PhotoItemSizeDynamic",
              "maxHeight": 1329,
              "maxWidth": 886,
              "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/05/4c/29/7e/lobby.jpg?w={width}&h={height}&s=1"
            }
          },
          {
            "__typename": "AppPresentation_PhotoItem",
            "sizes": {
              "__typename": "AppPresentation_PhotoItemSizeDynamic",
              "maxHeight": 886,
              "maxWidth": 1297,
              "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/05/4c/29/83/bathroom.jpg?w={width}&h={height}&s=1"
            }
          }
        ]
      },
      {
        "id": "17413751",
        "title": "30. The Park Mumbai",
        "primaryInfo": "Free breakfast included",
        "secondaryInfo": "Juhu",
        "badge": {
          "size": "SMALL",
          "type": "TRAVELLER_CHOICE",
          "year": "2022"
        },
        "bubbleRating": {
          "count": "259",
          "rating": 5
        },
        "isSponsored": false,
        "accentedLabel": false,
        "provider": "FindHotel",
        "priceForDisplay": null,
        "strikethroughPrice": null,
        "priceDetails": null,
        "priceSummary": null,
        "cardPhotos": [
          {
            "__typename": "AppPresentation_PhotoItem",
            "sizes": {
              "__typename": "AppPresentation_PhotoItemSizeDynamic",
              "maxHeight": 803,
              "maxWidth": 1200,
              "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1b/b6/55/e6/hotel-lobby.jpg?w={width}&h={height}&s=1"
            }
          },
          {
            "__typename": "AppPresentation_PhotoItem",
            "sizes": {
              "__typename": "AppPresentation_PhotoItemSizeDynamic",
              "maxHeight": 4624,
              "maxWidth": 3699,
              "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1b/b8/ec/9a/the-park-mumbai.jpg?w={width}&h={height}&s=1"
            }
          },
          {
            "__typename": "AppPresentation_PhotoItem",
            "sizes": {
              "__typename": "AppPresentation_PhotoItemSizeDynamic",
              "maxHeight": 4000,
              "maxWidth": 3924,
              "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1b/b8/ec/50/the-park-mumbai.jpg?w={width}&h={height}&s=1"
            }
          },
          {
            "__typename": "AppPresentation_PhotoItem",
            "sizes": {
              "__typename": "AppPresentation_PhotoItemSizeDynamic",
              "maxHeight": 4265,
              "maxWidth": 3412,
              "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1b/b8/ec/12/the-park-mumbai.jpg?w={width}&h={height}&s=1"
            }
          }
        ]
      }
    ]
  }
}
        '''
        return hotel_data.get("data", {}).get("data", []) if hotel_data else []

    async def get_hotel_details(self, hotel_id, currency="USD"):
        """
        Retrieves details for a specific hotel asynchronously.

        Args:
            hotel_id (str): The ID of the hotel.
            currency (str, optional): The currency for pricing. Defaults to "USD".

        Returns:
            dict: The details of the specified hotel.
        """

        '''
        
        {
  "status": true,
  "message": "Success",
  "timestamp": 1661619809941,
  "data": {
    "photos": [
      {
        "maxHeight": 1733,
        "maxWidth": 2600,
        "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0e/e5/ee/a4/superior-luxury-room--v15259560.jpg?w={width}&h={height}&s=1"
      },
      {
        "maxHeight": 886,
        "maxWidth": 1737,
        "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/05/4c/29/80/bedroom.jpg?w={width}&h={height}&s=1"
      },
      {
        "maxHeight": 1329,
        "maxWidth": 886,
        "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/05/4c/29/7e/lobby.jpg?w={width}&h={height}&s=1"
      },
      {
        "maxHeight": 886,
        "maxWidth": 1297,
        "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/05/4c/29/83/bathroom.jpg?w={width}&h={height}&s=1"
      },
      {
        "maxHeight": 1440,
        "maxWidth": 960,
        "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/05/6a/33/4f/bathroom.jpg?w={width}&h={height}&s=1"
      },
      {
        "maxHeight": 1440,
        "maxWidth": 960,
        "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/05/6a/33/53/abode-bombay.jpg?w={width}&h={height}&s=1"
      },
      {
        "maxHeight": 1388,
        "maxWidth": 960,
        "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/05/6a/33/52/abode-bombay.jpg?w={width}&h={height}&s=1"
      },
      {
        "maxHeight": 960,
        "maxWidth": 1440,
        "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/05/6a/33/50/luxury-room.jpg?w={width}&h={height}&s=1"
      },
      {
        "maxHeight": 960,
        "maxWidth": 1440,
        "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/05/6a/33/54/basic-room.jpg?w={width}&h={height}&s=1"
      },
      {
        "maxHeight": 886,
        "maxWidth": 1387,
        "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/05/4c/29/87/cafe.jpg?w={width}&h={height}&s=1"
      }
    ],
    "title": "Abode Bombay",
    "rating": 4.5,
    "numberReviews": 1037,
    "rankingDetails": "#1 of 568 hotels in <a>Mumbai</a>",
    "price": {
      "displayPrice": null,
      "strikeThroughPrice": null,
      "status": "IN_PROGRESS",
      "providerName": "Booking.com",
      "freeCancellation": null,
      "pricingPeriod": null
    },
    "about": {
      "title": "Abode Bombay; the city's first authentic boutique hotel. The ultimate anti-chain hotel, Abode is fabulously unconventional in its individuality and style, yet suitably refined when it comes to meeting guests’ expectations. Abode defines a new breed of independent hotel, offering a refreshing contemporary approach to the modern global explorer who seeks an authentic, personal and genuinely engaging experience.",
      "content": [
        {
          "title": "Available languages",
          "content": [
            {
              "title": "",
              "content": "English, Hindi"
            }
          ]
        },
        {
          "title": "Amenities",
          "content": [
            {
              "title": "Free High Speed Internet (WiFi)"
            },
            {
              "title": "Free breakfast"
            },
            {
              "title": "Airport transportation"
            },
            {
              "title": "24-hour security"
            }
          ]
        }
      ],
      "tags": [
        "Quiet",
        "Modern",
        "Centrally Located",
        "Quaint"
      ]
    },
    "reviews": {
      "content": [
        {
          "title": "Abode visit",
          "text": "We had an excellent stay at Abode and would highly recommend it to anyone visiting Mumbai. Abode provided transportation from a woman-run taxi service which picked us up from the airport as well as dropped us off early in the morning (4AM)  at the train station. Not only was this service smooth, but also provides jobs to local women, particularly single mothers or widows, which was a nice touch. <br /><br />Upon arrival, we were offered an in depth explanation of local sites including restaurants, markets, and historical sites. We decided to do the street food tour, led by Vasu, which we would also highly recommend. The tour visited local markets and allowed us to try different types of street food. We were a bit hesitant to try street food without a guide, but Vasu did an excellent job, and we were able to sample some amazing food with the comfort of not worrying about “Delhi Belly” after eating. <br /><br />We also got massages offered by Abode. While the spa set up was somewhat simplistic, the massages were great and were done by blind locals, which provides them with jobs which again was a nice touch.<br /><br />The rooms were very clean and the beds were comfortable. Abode is also zero waste, and offered filtered water in glass bottles which was a welcome change from all of the plastic water bottles we had used previously on our trip. Our departure train was very early in the morning, and Abode provided us with sandwiches for the train and a light breakfast which was great. Overall the stay was amazing and we would definitely stay there again!",
          "bubbleRatingText": "Couples",
          "publishedDate": "Written 11/08/22",
          "userProfile": {
            "deprecatedContributionCount": "5 contributions",
            "avatar": {
              "maxHeight": 205,
              "maxWidth": 205,
              "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-f/01/2e/70/83/avatar004.jpg?w={width}&h={height}&s=1"
            }
          },
          "photos": []
        },
        {
          "title": "A bit over hyped Botique hotel",
          "text": "We took two rooms, one for us as a couple with two small children, one for our parents. One was a Superior Luxury room and one was a Luxury room. The difference between Superior and not-superior was the availability of a bathtub in the middle of the room. <br />Pros:<br />The rooms were charming, nicely decorated with vintage photographs and old style furniture. <br />The staff were courteous, always willing to help.<br />Location, very very close to the Gateway of India.<br />Cons:<br />Ok we should be honest, this hotel would have been great for young travellers who dont have any specific needs. If you go with young children, you need to note - there is no bottled water as they are plastic free, no kettle to boil the water they give, which you generally expect in a hotel at this cost. Once I tried request for warm water from the staff and I got it in a very dirty cup sadly. If it is just us as a couple, we wouldnt have found this a big discomfort. <br />Location - though it was a pro because it is close to attractions, it is a con because it is a very cramped road and the hotel is not visible at all from the road. If you are super comfortable in hailing taxis in Indian cities, you can manage. Sometimes Uber/Ola drops you somewhere on the road. Surprisingly, I couldnt find many convenience stores in the area that is supposedly a very busy market place.<br />They did not come for housekeeping until we called. We did go out during the day, but when we came back the bed was not made and trash was not emptied. As they were a plastic free hotel, there was a beautiful copper water pot used as a trash can. Though it was beautiful, it was super full very fast. But once we called they did come and clean.<br /><br />Overall, we were having issues only because we had old parents and young kids with us in the trip. If you are backpacking travellers, you may love this hotel and have a lot of fun.",
          "bubbleRatingText": "",
          "publishedDate": "Written 09/06/22",
          "userProfile": {
            "deprecatedContributionCount": "27 contributions",
            "avatar": {
              "maxHeight": 1200,
              "maxWidth": 1200,
              "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1a/f6/ea/74/default-avatar-2020-68.jpg?w={width}&h={height}&s=1"
            }
          },
          "photos": []
        }
      ],
      "count": 1037,
      "ratingValue": 4.5,
      "ratingCounts": {
        "average": {
          "percentage": 3,
          "count": "35"
        },
        "excellent": {
          "percentage": 81,
          "count": "835"
        },
        "poor": {
          "percentage": 1,
          "count": "12"
        },
        "terrible": {
          "percentage": 1,
          "count": "7"
        },
        "veryGood": {
          "percentage": 14,
          "count": "148"
        }
      }
    },
    "location": {
      "title": "The area",
      "address": "Lansdowne House M.B. Marg, behind Regal Cinema, Mumbai 400001 India",
      "neighborhood": {
        "name": "Wellington Pier",
        "text": null
      },
      "gettingThere": {
        "title": "How to get there",
        "content": [
          "Mumbai Airport • 19 km"
        ]
      },
      "walkability": null
    },
    "geoPoint": {
      "latitude": 18.92383,
      "longitude": 72.8325
    },
    "restaurantsNearby": {
      "sectionTitle": "Restaurants nearby",
      "content": [
        {
          "title": "Shamiana",
          "bubbleRating": {
            "rating": 4.5,
            "numberReviews": "568"
          },
          "primaryInfo": "₹₹₹₹ • American • Indian • International",
          "distance": "0.2 km",
          "cardPhoto": {
            "maxHeight": 1280,
            "maxWidth": 1596,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0c/f3/dd/5f/homemade-pancakes.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Sea Lounge",
          "bubbleRating": {
            "rating": 4.5,
            "numberReviews": "1,137"
          },
          "primaryInfo": "₹₹₹₹ • Indian • International • Vegetarian Friendly",
          "distance": "0.2 km",
          "cardPhoto": {
            "maxHeight": 1400,
            "maxWidth": 2000,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0d/f2/ac/a3/sea-lounge.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Souk",
          "bubbleRating": {
            "rating": 4.5,
            "numberReviews": "358"
          },
          "primaryInfo": "₹₹₹₹ • Lebanese • Mediterranean • Turkish",
          "distance": "0.3 km",
          "cardPhoto": {
            "maxHeight": 1335,
            "maxWidth": 2000,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0d/f2/87/2a/souk.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Bombay Vintage",
          "bubbleRating": {
            "rating": 4.5,
            "numberReviews": "224"
          },
          "primaryInfo": "₹₹ - ₹₹₹ • Indian • Bar • Vegetarian Friendly",
          "distance": "0.2 km",
          "cardPhoto": {
            "maxHeight": 628,
            "maxWidth": 1200,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/16/c6/19/17/spread.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Golden Dragon",
          "bubbleRating": {
            "rating": 4.5,
            "numberReviews": "439"
          },
          "primaryInfo": "₹₹₹₹ • Chinese • Cantonese • Szechuan",
          "distance": "0.2 km",
          "cardPhoto": {
            "maxHeight": 1500,
            "maxWidth": 1970,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0d/f2/8c/b7/golden-dragon.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "The Table",
          "bubbleRating": {
            "rating": 4.5,
            "numberReviews": "532"
          },
          "primaryInfo": "₹₹₹₹ • International • European • Vegetarian Friendly",
          "distance": "71 m",
          "cardPhoto": {
            "maxHeight": 361,
            "maxWidth": 550,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-s/02/96/d3/ab/filename-mezzanine-jpg.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Woodside Inn",
          "bubbleRating": {
            "rating": 4,
            "numberReviews": "294"
          },
          "primaryInfo": "₹₹ - ₹₹₹ • Italian • Bar • European",
          "distance": "0.1 km",
          "cardPhoto": {
            "maxHeight": 675,
            "maxWidth": 1200,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1b/00/c3/7c/interior.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Smoke House Deli",
          "bubbleRating": {
            "rating": 4,
            "numberReviews": "276"
          },
          "primaryInfo": "₹₹ - ₹₹₹ • Italian • European • Vegetarian Friendly",
          "distance": "0.2 km",
          "cardPhoto": {
            "maxHeight": 750,
            "maxWidth": 1000,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1a/b3/87/de/img-20200125-130008-largejpg.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Cafe Mondegar",
          "bubbleRating": {
            "rating": 4,
            "numberReviews": "1,636"
          },
          "primaryInfo": "₹₹ - ₹₹₹ • Indian • Vegetarian Friendly • Vegan Options",
          "distance": "55 m",
          "cardPhoto": {
            "maxHeight": 452,
            "maxWidth": 678,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/15/eb/35/34/cafe-mondegar.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Masala Kraft",
          "bubbleRating": {
            "rating": 4,
            "numberReviews": "420"
          },
          "primaryInfo": "₹₹₹₹ • Indian • Asian • Vegetarian Friendly",
          "distance": "0.2 km",
          "cardPhoto": {
            "maxHeight": 1500,
            "maxWidth": 2000,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/13/28/48/c8/lovely-classy-interiors.jpg?w={width}&h={height}&s=1"
          }
        }
      ]
    },
    "attractionsNearby": {
      "sectionTitle": "Attractions nearby",
      "content": [
        {
          "title": "Popli Art Gallery",
          "bubbleRating": {
            "rating": 5,
            "numberReviews": "3"
          },
          "primaryInfo": "Art Galleries",
          "distance": "41 m",
          "cardPhoto": {}
        },
        {
          "title": "Gateway of India",
          "bubbleRating": {
            "rating": 4,
            "numberReviews": "12,497"
          },
          "primaryInfo": "Points of Interest & Landmarks • Monuments & Statues",
          "distance": "0.3 km",
          "cardPhoto": {
            "maxHeight": 642,
            "maxWidth": 960,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0d/16/f3/a1/fb-img-1474806779807.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Cathedral of the Holy Name",
          "bubbleRating": {
            "rating": 4.5,
            "numberReviews": "34"
          },
          "primaryInfo": "Churches & Cathedrals",
          "distance": "0.2 km",
          "cardPhoto": {
            "maxHeight": 3648,
            "maxWidth": 5472,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/17/21/3d/48/interno.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Bowen Memorial Methodist Church",
          "bubbleRating": {
            "rating": 4.5,
            "numberReviews": "4"
          },
          "primaryInfo": "Historic Sites • Churches & Cathedrals",
          "distance": "0.1 km",
          "cardPhoto": {
            "maxHeight": 2048,
            "maxWidth": 1638,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0e/42/82/ef/church-view-from-the.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Flora Fountain",
          "bubbleRating": {
            "rating": 4,
            "numberReviews": "217"
          },
          "primaryInfo": "Points of Interest & Landmarks • Fountains",
          "distance": "0.2 km",
          "cardPhoto": {
            "maxHeight": 1500,
            "maxWidth": 2000,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/05/a7/98/8b/flora-fountain.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Lion Gate",
          "bubbleRating": {
            "rating": 3,
            "numberReviews": "27"
          },
          "primaryInfo": "Points of Interest & Landmarks",
          "distance": "0.2 km",
          "cardPhoto": {
            "maxHeight": 1936,
            "maxWidth": 2592,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/07/f1/9b/9f/caption.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "L.B. Shastri Statue- Jai Jawan Jai Kisan",
          "bubbleRating": {
            "rating": 3,
            "numberReviews": "1"
          },
          "primaryInfo": "Monuments & Statues",
          "distance": "0.1 km",
          "cardPhoto": {
            "maxHeight": 1152,
            "maxWidth": 648,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1a/30/0e/f3/statue-of-lal-bahadur.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Statue Of Chhatrapati Shivaji Maharaj",
          "bubbleRating": {
            "rating": 3.5,
            "numberReviews": "11"
          },
          "primaryInfo": "Points of Interest & Landmarks • Monuments & Statues",
          "distance": "0.2 km",
          "cardPhoto": {
            "maxHeight": 2000,
            "maxWidth": 1125,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/12/3f/41/ff/impressive-statue.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Colaba",
          "bubbleRating": {
            "rating": 4.5,
            "numberReviews": "2,494"
          },
          "primaryInfo": "Neighbourhoods",
          "distance": "0.3 km",
          "cardPhoto": {
            "maxHeight": 1338,
            "maxWidth": 1999,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/07/38/3d/94/colaba.jpg?w={width}&h={height}&s=1"
          }
        },
        {
          "title": "Chhatrapati Shivaji Maharaj Vastu Sangrahalaya",
          "bubbleRating": {
            "rating": 4.5,
            "numberReviews": "966"
          },
          "primaryInfo": "History Museums",
          "distance": "0.3 km",
          "cardPhoto": {
            "maxHeight": 1500,
            "maxWidth": 2000,
            "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/11/0c/42/80/museum-visit.jpg?w={width}&h={height}&s=1"
          }
        }
      ]
    },
    "qA": {
      "content": [
        {
          "title": "Is this place suitable for a family of 5?",
          "writtenDate": "12 March 2022",
          "memberProfile": {
            "profileImage": {}
          },
          "topAnswer": {
            "text": "Hi...We had booked their superior deluxe room and were a family of 3 but it was just right for us. They might have bigger rooms for a family of 5 but I cannot confirm that. You can email Nelcia at their email id. She is super helpful. Hope this helps.",
            "writtenDate": "12 March 2022",
            "thumbsUpCount": 0,
            "memberProfile": {
              "displayName": "Jyo Dmello",
              "hometown": null,
              "profileImage": {
                "maxHeight": 3024,
                "maxWidth": 3024,
                "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/24/7b/28/22/alisong1038.jpg?w={width}&h={height}&s=1"
              },
              "contributionCounts": null,
              "deprecatedContributionCount": "1 contribution"
            }
          }
        },
        {
          "title": "Is it a couple friendly hotel?\n",
          "writtenDate": "6 September 2020",
          "memberProfile": {
            "profileImage": {}
          },
          "topAnswer": {
            "text": "Definitly",
            "writtenDate": "7 September 2020",
            "thumbsUpCount": 0,
            "memberProfile": {
              "displayName": "Darren",
              "hometown": null,
              "profileImage": {
                "maxHeight": 1200,
                "maxWidth": 1200,
                "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1a/f6/f4/5d/default-avatar-2020-32.jpg?w={width}&h={height}&s=1"
              },
              "contributionCounts": null,
              "deprecatedContributionCount": "4 contributions"
            }
          }
        }
      ]
    },
    "amenitiesScreen": [
      {
        "title": "Internet",
        "content": [
          "Free High Speed Internet (WiFi)",
          "Wifi"
        ]
      },
      {
        "title": "Food & drink",
        "content": [
          "Free breakfast",
          "Breakfast buffet",
          "Special diet menus"
        ]
      },
      {
        "title": "Transportation",
        "content": [
          "Airport transportation",
          "Taxi service"
        ]
      },
      {
        "title": "General",
        "content": [
          "24-hour security",
          "Baggage storage",
          "Concierge",
          "Currency exchange",
          "Newspaper",
          "Non-smoking hotel",
          "Shared lounge / TV area"
        ]
      },
      {
        "title": "Reception services",
        "content": [
          "24-hour check-in",
          "24-hour front desk",
          "Private check-in / check-out"
        ]
      },
      {
        "title": "Cleaning services",
        "content": [
          "Dry cleaning",
          "Laundry service",
          "Ironing service"
        ]
      },
      {
        "title": "Room types",
        "content": [
          "Non-smoking rooms"
        ]
      },
      {
        "title": "Room features",
        "content": [
          "Air conditioning",
          "Safe",
          "Bottled water",
          "Wake-up service / alarm clock"
        ]
      },
      {
        "title": "Entertainment",
        "content": [
          "Flatscreen TV"
        ]
      }
    ]
  }
}
        '''


        return await self._make_request("GET", "/hotels/getHotelDetails", params={"id": hotel_id, "checkIn":"2025-08-11", "checkOut":"2025-08-15", "currency": currency})

    async def search_restaurants_by_city(self, city_name, currency="USD"):
        """
        Searches for restaurants in a given city asynchronously.

        Args:
            city_name (str): The name of the city to search for restaurants in.
            currency (str, optional): The currency for pricing. Defaults to "USD".

        Returns:
            list: A list of restaurants found in the specified city.
        """
        # 1. Get location ID for the city
        location_data = await self._make_request("GET", "/restaurant/searchLocation", params={"query": city_name})
        if not location_data or "data" not in location_data or not location_data["data"]:
            return []
            
        try:
            location_id = location_data["data"][0]["locationId"]
        except (KeyError, IndexError):
            print(f"Could not find locationId for city: {city_name}")
            return []

        '''
        {
  "status": true,
  "message": "Success",
  "timestamp": 1664130190825,
  "data": [
    {
      "documentId": "304554",
      "locationId": 304554,
      "localizedName": "Mumbai",
      "localizedAdditionalNames": {
        "longOnlyHierarchy": "Maharashtra, India, Asia"
      },
      "streetAddress": {
        "street1": ""
      },
      "locationV2": {
        "placeType": "CITY",
        "names": {
          "longOnlyHierarchyTypeaheadV2": "Maharashtra, India"
        },
        "vacationRentalsRoute": {
          "url": "/VacationRentals-g304554-Reviews-Mumbai_Maharashtra-Vacation_Rentals.html"
        }
      },
      "placeType": "CITY",
      "latitude": 18.936844,
      "longitude": 72.8291,
      "isGeo": true,
      "thumbnail": {
        "photoSizeDynamic": {
          "maxWidth": 5328,
          "maxHeight": 3000,
          "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0b/4e/55/e6/chhatrapati-shivaji-terminus.jpg?w={width}&h={height}&s=1"
        }
      }
    },
    {
      "documentId": "17643064",
      "locationId": 17643064,
      "localizedName": "Mumbai Kitchen",
      "localizedAdditionalNames": {
        "longOnlyHierarchy": "Canggu, North Kuta, Bali, Indonesia, Asia"
      },
      "streetAddress": {
        "street1": "Jalan Pantai Berawa"
      },
      "locationV2": {
        "placeType": "EATERY",
        "names": {
          "longOnlyHierarchyTypeaheadV2": "Canggu, Indonesia"
        },
        "vacationRentalsRoute": null
      },
      "placeType": "EATERY",
      "latitude": -8.655116,
      "longitude": 115.1479,
      "isGeo": false,
      "thumbnail": {
        "photoSizeDynamic": {
          "maxWidth": 2975,
          "maxHeight": 2975,
          "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/18/2a/8b/67/mumbai-kitchen-logo.jpg?w={width}&h={height}&s=1"
        }
      }
    },
    {
      "documentId": "18380500",
      "locationId": 18380500,
      "localizedName": "Mumbai Masala Puerto Calero",
      "localizedAdditionalNames": {
        "longOnlyHierarchy": "Yaiza, Lanzarote, Canary Islands, Spain, Europe"
      },
      "streetAddress": {
        "street1": "Paseo Marítimo Puerto Calero"
      },
      "locationV2": {
        "placeType": "EATERY",
        "names": {
          "longOnlyHierarchyTypeaheadV2": "Yaiza, Lanzarote, Spain"
        },
        "vacationRentalsRoute": null
      },
      "placeType": "EATERY",
      "latitude": 28.917103,
      "longitude": -13.703982,
      "isGeo": false,
      "thumbnail": {
        "photoSizeDynamic": {
          "maxWidth": 3024,
          "maxHeight": 4032,
          "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1d/a3/e3/8b/mumbai-masala-puerto.jpg?w={width}&h={height}&s=1"
        }
      }
    },
    {
      "documentId": "12450817",
      "locationId": 12450817,
      "localizedName": "Mumbai Masala Jameos",
      "localizedAdditionalNames": {
        "longOnlyHierarchy": "Puerto Del Carmen, Lanzarote, Canary Islands, Spain, Europe"
      },
      "streetAddress": {
        "street1": "Avenida Playas 100"
      },
      "locationV2": {
        "placeType": "EATERY",
        "names": {
          "longOnlyHierarchyTypeaheadV2": "Puerto Del Carmen, Lanzarote, Spain"
        },
        "vacationRentalsRoute": null
      },
      "placeType": "EATERY",
      "latitude": 28.9281,
      "longitude": -13.628911,
      "isGeo": false,
      "thumbnail": {
        "photoSizeDynamic": {
          "maxWidth": 2048,
          "maxHeight": 1536,
          "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/10/76/7c/a5/mumbai-masala-jameos.jpg?w={width}&h={height}&s=1"
        }
      }
    },
    {
      "documentId": "15263511",
      "locationId": 15263511,
      "localizedName": "Mumbai Masala Playa Paraíso",
      "localizedAdditionalNames": {
        "longOnlyHierarchy": "Playa Paraiso, Adeje, Tenerife, Canary Islands, Spain, Europe"
      },
      "streetAddress": {
        "street1": "Numero 16, C.C. Paraiso sur 12 Avenida Adeje 300"
      },
      "locationV2": {
        "placeType": "EATERY",
        "names": {
          "longOnlyHierarchyTypeaheadV2": "Playa Paraiso, Tenerife, Spain"
        },
        "vacationRentalsRoute": null
      },
      "placeType": "EATERY",
      "latitude": 28.121693,
      "longitude": -16.775276,
      "isGeo": false,
      "thumbnail": {
        "photoSizeDynamic": {
          "maxWidth": 1116,
          "maxHeight": 628,
          "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/15/26/f8/65/foto.jpg?w={width}&h={height}&s=1"
        }
      }
    },
    {
      "documentId": "15187799",
      "locationId": 15187799,
      "localizedName": "Mumbai Darbar Indian Restaurant",
      "localizedAdditionalNames": {
        "longOnlyHierarchy": "Alvor, Portimao, Faro District, Algarve, Portugal, Europe"
      },
      "streetAddress": {
        "street1": "Rua do Rossio Grande"
      },
      "locationV2": {
        "placeType": "EATERY",
        "names": {
          "longOnlyHierarchyTypeaheadV2": "Alvor, Portugal"
        },
        "vacationRentalsRoute": null
      },
      "placeType": "EATERY",
      "latitude": 37.12881,
      "longitude": -8.590189,
      "isGeo": false,
      "thumbnail": {
        "photoSizeDynamic": {
          "maxWidth": 4032,
          "maxHeight": 3024,
          "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1c/00/dc/7a/indian-curry-house-alvor.jpg?w={width}&h={height}&s=1"
        }
      }
    },
    {
      "documentId": "1317396",
      "locationId": 1317396,
      "localizedName": "Mumbai Delight",
      "localizedAdditionalNames": {
        "longOnlyHierarchy": "London, England, United Kingdom, Europe"
      },
      "streetAddress": {
        "street1": "51A South Lambeth Road"
      },
      "locationV2": {
        "placeType": "EATERY",
        "names": {
          "longOnlyHierarchyTypeaheadV2": "London, England"
        },
        "vacationRentalsRoute": null
      },
      "placeType": "EATERY",
      "latitude": 51.482285,
      "longitude": -0.124273,
      "isGeo": false,
      "thumbnail": {
        "photoSizeDynamic": {
          "maxWidth": 1125,
          "maxHeight": 1500,
          "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/12/a6/ca/a6/samosas.jpg?w={width}&h={height}&s=1"
        }
      }
    },
    {
      "documentId": "3807659",
      "locationId": 3807659,
      "localizedName": "Mumbai Times",
      "localizedAdditionalNames": {
        "longOnlyHierarchy": "Cos Cob, Connecticut, United States, North America"
      },
      "streetAddress": {
        "street1": "140 E Putnam Ave"
      },
      "locationV2": {
        "placeType": "EATERY",
        "names": {
          "longOnlyHierarchyTypeaheadV2": "Cos Cob, Connecticut"
        },
        "vacationRentalsRoute": null
      },
      "placeType": "EATERY",
      "latitude": 41.03768,
      "longitude": -73.60096,
      "isGeo": false,
      "thumbnail": {
        "photoSizeDynamic": {
          "maxWidth": 1632,
          "maxHeight": 1224,
          "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/04/20/dd/97/mumbai-times.jpg?w={width}&h={height}&s=1"
        }
      }
    },
    {
      "documentId": "10516202",
      "locationId": 10516202,
      "localizedName": "Mumbai Masala",
      "localizedAdditionalNames": {
        "longOnlyHierarchy": "Puerto Del Carmen, Lanzarote, Canary Islands, Spain, Europe"
      },
      "streetAddress": {
        "street1": "Avenida Playas 15"
      },
      "locationV2": {
        "placeType": "EATERY",
        "names": {
          "longOnlyHierarchyTypeaheadV2": "Puerto Del Carmen, Lanzarote, Spain"
        },
        "vacationRentalsRoute": null
      },
      "placeType": "EATERY",
      "latitude": 28.920832,
      "longitude": -13.662196,
      "isGeo": false,
      "thumbnail": {
        "photoSizeDynamic": {
          "maxWidth": 1358,
          "maxHeight": 1240,
          "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0c/11/07/a9/mumbai-masala.jpg?w={width}&h={height}&s=1"
        }
      }
    }
  ]
}
        '''



        # 2. Search for restaurants using the location ID
        restaurant_data = await self._make_request("GET", "/restaurant/searchRestaurants", params={"locationId": location_id, "currency": currency})

        '''
        {
        "status": true,
        "message": "Success",
        "timestamp": 1754819060621,
        "data": {
            "totalRecords": 10000,
            "totalPages": 333,
            "data": [
            {
                "restaurantsId": "Restaurant_Review-g304554-d10539996-Reviews-Dashanzi-Mumbai_Maharashtra",
                "locationId": 10539996,
                "name": "Dashanzi",
                "averageRating": 4.9,
                "userReviewCount": 478,
                "currentOpenStatusCategory": "CLOSING",
                "currentOpenStatusText": "Closes in 15 min",
                "priceTag": "$$$$",
                "hasMenu": true,
                "menuUrl": "https://bit.ly/3R7sjh7",
                "isDifferentGeo": false,
                "parentGeoName": "Mumbai",
                "distanceTo": null,
                "awardInfo": null,
                "isLocalChefItem": false,
                "isPremium": false,
                "isStoryboardPublished": false,
                "establishmentTypeAndCuisineTags": [
                "Chinese",
                "Japanese",
                "Sushi",
                "Asian"
                ],
                "offers": {
                "hasDelivery": false,
                "hasReservation": true,
                "slot1Offer": {
                    "providerId": "14051",
                    "provider": "Restaurants_SevenRooms",
                    "providerDisplayName": "SevenRooms",
                    "buttonText": "Reserve",
                    "offerURL": "YjRWXy9Db21tZXJjZT9wPVJlc3RhdXJhbnRzX1NldmVuUm9vbXMmc3JjPTI1MzU2OTQ0NCZnZW89MTA1Mzk5OTYmZnJvbT1SZXN0YXVyYW50cyZhcmVhPXJlc2VydmF0aW9uX2J1dHRvbiZzbG90PTEmbWF0Y2hJRD0xJm9vcz0wJmNudD0xJnNpbG89MjkwMjUmYnVja2V0PTg3MDgxMyZucmFuaz0xJmNyYW5rPTEmY2x0PVImdHR5cGU9UmVzdGF1cmFudCZ0bT0zMzQ3MzA2NjAmbWFuYWdlZD1mYWxzZSZjYXBwZWQ9ZmFsc2UmZ29zb3g9RTRkUzZCbUJHZHJyMnFlRU1meU00WWtoN2c3a1paTVF0d3ZYMXI3LWJabjBTRzh3aS1jT2llb0RSMWVNak90Uk5HaTlJNm51QlBtWG11blQyRjdZMmVHNHRCUi1qc3pfVEhVWkEtYUhUQ1kmY3M9MTc4ODRkZjlmMmZmYTIwZDcyNjNhZThlMDExOTBkNjdkX0tpaQ==",
                    "logoUrl": "/img2/branding/hotels/sevenrooms_04.23.2019.png",
                    "trackingEvent": "reserve_click",
                    "canProvideTimeslots": false,
                    "canLockTimeslots": false,
                    "timeSlots": []
                },
                "slot2Offer": null,
                "restaurantSpecialOffer": null
                },
                "heroImgUrl": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0c/9b/cf/47/bar.jpg?w=1600&h=1200&s=1",
                "heroImgRawHeight": 1200,
                "heroImgRawWidth": 1694,
                "squareImgUrl": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0c/9b/cf/47/bar.jpg?w=200&h=200&s=1",
                "squareImgRawLength": 0,
                "thumbnail": {
                "photo": {
                    "photoSizeDynamic": {
                    "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0c/9b/cf/47/bar.jpg?w={width}&h={height}&s=1",
                    "maxHeight": 1200,
                    "maxWidth": 1694
                    }
                }
                },
                "reviewSnippets": {
                "reviewSnippetsList": [
                    {
                    "reviewText": "... cones to the edamame truffle ￹dumplings￻ and finally the dessert, everythin...",
                    "reviewUrl": "https://www.tripadvisor.com/ShowUserReviews-g304554-d10539996-r986668979-Dashanzi-Mumbai_Maharashtra.html"
                    },
                    {
                    "reviewText": "You’ll find the most delicious ￹Sushi￻ an...",
                    "reviewUrl": "https://www.tripadvisor.com/ShowUserReviews-g304554-d10539996-r1003669404-Dashanzi-Mumbai_Maharashtra.html"
                    }
                ]
                }
            },
            
            {
                "restaurantsId": "Restaurant_Review-g304554-d21511592-Reviews-Rasoi_Kitchen_Bar-Mumbai_Maharashtra",
                "locationId": 21511592,
                "name": "Rasoi Kitchen & Bar",
                "averageRating": 4.9,
                "userReviewCount": 205,
                "currentOpenStatusCategory": "OPEN",
                "currentOpenStatusText": "Open now",
                "priceTag": "$$ - $$$",
                "hasMenu": false,
                "menuUrl": null,
                "isDifferentGeo": false,
                "parentGeoName": "Mumbai",
                "distanceTo": null,
                "awardInfo": null,
                "isLocalChefItem": false,
                "isPremium": false,
                "isStoryboardPublished": false,
                "establishmentTypeAndCuisineTags": [
                "Indian",
                "Asian",
                "Middle Eastern"
                ],
                "offers": {
                "hasDelivery": null,
                "hasReservation": null,
                "slot1Offer": null,
                "slot2Offer": null,
                "restaurantSpecialOffer": null
                },
                "heroImgUrl": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1c/6d/d9/04/come-to-rasoi-and-discover.jpg?w=1500&h=2200&s=1",
                "heroImgRawHeight": 2245,
                "heroImgRawWidth": 1587,
                "squareImgUrl": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1c/6d/d9/04/come-to-rasoi-and-discover.jpg?w=200&h=200&s=1",
                "squareImgRawLength": 0,
                "thumbnail": {
                "photo": {
                    "photoSizeDynamic": {
                    "urlTemplate": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1c/6d/d9/04/come-to-rasoi-and-discover.jpg?w={width}&h={height}&s=1",
                    "maxHeight": 2245,
                    "maxWidth": 1587
                    }
                }
                },
                "reviewSnippets": {
                "reviewSnippetsList": [
                    {
                    "reviewText": "Bhati Da ￹Murg￻- It was having an amazing taste of spices and the chicken was c...",
                    "reviewUrl": "https://www.tripadvisor.com/ShowUserReviews-g304554-d21511592-r904382187-Rasoi_Kitchen_Bar-Mumbai_Maharashtra.html"
                    },
                    {
                    "reviewText": "Best ￹Indian￻ and Chinese Cuisine restaurant",
                    "reviewUrl": "https://www.tripadvisor.com/ShowUserReviews-g304554-d21511592-r875850143-Rasoi_Kitchen_Bar-Mumbai_Maharashtra.html"
                    }
                ]
                }
            }
            ],
            "currentPage": 1
        }
        }
        '''


        return restaurant_data.get("data", {}).get("data", []) if restaurant_data else []

    async def get_restaurant_details(self, restaurant_id, currency="USD"):
        """
        Retrieves details for a specific restaurant using the V2 endpoint asynchronously.

        Args:
            restaurant_id (str): The ID of the restaurant.
            currency (str, optional): The currency for pricing. Defaults to "USD".

        Returns:
            dict: The details of the specified restaurant.
        """

        """
        {
  "status": true,
  "message": "Success",
  "timestamp": 1665486760272,
  "data": {
    "location": {
      "location_id": "8010527",
      "name": "Saptami",
      "latitude": "19.103235",
      "longitude": "72.88693",
      "num_reviews": "720",
      "timezone": "Asia/Kolkata",
      "location_string": "Mumbai, Maharashtra",
      "awards": [],
      "doubleclick_zone": "as.india.mumbai",
      "preferred_map_engine": "default",
      "raw_ranking": "4.900440216064453",
      "ranking_geo": "Mumbai",
      "ranking_geo_id": "304554",
      "ranking_position": "2",
      "ranking_denominator": "9260",
      "ranking_category": "restaurant",
      "ranking": "#2 of 14,721 places to eat in Mumbai",
      "distance": null,
      "distance_string": null,
      "bearing": null,
      "rating": "5.0",
      "is_closed": false,
      "open_now_text": "Open Now",
      "is_long_closed": false,
      "price_level": "$$$$",
      "price": "$1,200 - $2,000",
      "neighborhood_info": [
        {
          "location_id": "15621370",
          "name": "Eastern Suburbs"
        },
        {
          "location_id": "15621447",
          "name": "Sakinaka"
        },
        {
          "location_id": "15621471",
          "name": "Western Suburbs"
        }
      ],
      "description": "Saptami - our all day dining restaurant offers authentic cuisines with efficient service and local knowledge. Saptami offers a plethora of cuisines like Indian, Continental, Oriental etc. It is close to both the terminals and north Mumbai business hubs with the international airport at 1.2 km and domestic airport at 5 km.",
      "web_url": "https://www.tripadvisor.com/Restaurant_Review-g304554-d8010527-Reviews-Saptami-Mumbai_Maharashtra.html",
      "write_review": "https://www.tripadvisor.com/UserReview-g304554-d8010527-Saptami-Mumbai_Maharashtra.html",
      "ancestors": [
        {
          "subcategory": [
            {
              "key": "city",
              "name": "City"
            }
          ],
          "name": "Mumbai",
          "abbrv": null,
          "location_id": "304554"
        },
        {
          "subcategory": [
            {
              "key": "state",
              "name": "State"
            }
          ],
          "name": "Maharashtra",
          "abbrv": null,
          "location_id": "297648"
        },
        {
          "subcategory": [
            {
              "key": "country",
              "name": "Country"
            }
          ],
          "name": "India",
          "abbrv": null,
          "location_id": "293860"
        }
      ],
      "category": {
        "key": "restaurant",
        "name": "Restaurant"
      },
      "subcategory": [
        {
          "key": "sit_down",
          "name": "Sit down"
        }
      ],
      "parent_display_name": "Mumbai",
      "is_jfy_enabled": false,
      "nearest_metro_station": [],
      "website": "http://www.holidayinn.com/hotels/us/en/mumbai/bomap/hoteldetail/dining",
      "email": "saptami@himia.in",
      "address_obj": {
        "street1": "Holiday Inn Hotel, Lobby Level, Saki Naka Junction, Andheri Kurla Road, Andheri East",
        "street2": null,
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "postalcode": "400072"
      },
      "address": "Holiday Inn Hotel, Lobby Level, Saki Naka Junction, Andheri Kurla Road, Andheri East, Mumbai 400072 India",
      "hours": {
        "week_ranges": [
          [
            {
              "open_time": 420,
              "close_time": 1410
            }
          ],
          [
            {
              "open_time": 420,
              "close_time": 1410
            }
          ],
          [
            {
              "open_time": 420,
              "close_time": 1410
            }
          ],
          [
            {
              "open_time": 420,
              "close_time": 1410
            }
          ],
          [
            {
              "open_time": 420,
              "close_time": 1410
            }
          ],
          [
            {
              "open_time": 420,
              "close_time": 1410
            }
          ],
          [
            {
              "open_time": 420,
              "close_time": 1410
            }
          ]
        ],
        "timezone": "Asia/Kolkata"
      },
      "is_candidate_for_contact_info_suppression": false,
      "cuisine": [
        {
          "key": "10346",
          "name": "Indian"
        },
        {
          "key": "10659",
          "name": "Asian"
        },
        {
          "key": "10679",
          "name": "Healthy"
        },
        {
          "key": "10648",
          "name": "International"
        },
        {
          "key": "10665",
          "name": "Vegetarian Friendly"
        },
        {
          "key": "10697",
          "name": "Vegan Options"
        },
        {
          "key": "10751",
          "name": "Halal"
        },
        {
          "key": "10992",
          "name": "Gluten Free Options"
        }
      ],
      "dietary_restrictions": [
        {
          "key": "10665",
          "name": "Vegetarian Friendly"
        },
        {
          "key": "10697",
          "name": "Vegan Options"
        },
        {
          "key": "10751",
          "name": "Halal"
        },
        {
          "key": "10992",
          "name": "Gluten Free Options"
        }
      ],
      "photo": {
        "id": "341762257",
        "caption": "Saptami - A contemporary multi-cuisine all day dining restaurant ",
        "published_date": "2018-08-29T01:59:06-0400",
        "helpful_votes": "1",
        "is_blessed": false,
        "uploaded_date": "2018-08-29T01:59:06-0400",
        "images": {
          "small": {
            "url": "https://media-cdn.tripadvisor.com/media/photo-l/14/5e/e0/d1/saptami-a-contemporary.jpg",
            "width": "150",
            "height": "150"
          },
          "thumbnail": {
            "url": "https://media-cdn.tripadvisor.com/media/photo-t/14/5e/e0/d1/saptami-a-contemporary.jpg",
            "width": "50",
            "height": "50"
          },
          "original": {
            "url": "https://media-cdn.tripadvisor.com/media/photo-o/14/5e/e0/d1/saptami-a-contemporary.jpg",
            "width": "5616",
            "height": "3744"
          },
          "large": {
            "url": "https://media-cdn.tripadvisor.com/media/photo-s/14/5e/e0/d1/saptami-a-contemporary.jpg",
            "width": "550",
            "height": "367"
          },
          "medium": {
            "url": "https://media-cdn.tripadvisor.com/media/photo-f/14/5e/e0/d1/saptami-a-contemporary.jpg",
            "width": "250",
            "height": "167"
          }
        }
      },
      "tags": null,
      "display_hours": [
        {
          "days": "Sun - Sat",
          "times": [
            "7:00 AM - 11:30 PM"
          ]
        }
      ]
    },
    "hours": {
      "openStatus": "OPEN",
      "openStatusText": "Open Now",
      "hoursTodayText": "Hours Today: 7:00 AM - 11:30 PM",
      "currentHoursText": "7:00 AM - 11:30 PM",
      "allOpenHours": [
        {
          "days": "Sun - Sat",
          "times": [
            "7:00 AM - 11:30 PM"
          ]
        }
      ],
      "addHoursLink": {
        "url": "/UpdateListing-d8010527#Hours-only",
        "text": "+ Add hours"
      }
    },
    "ownerStatus": {
      "isVerified": true,
      "isMemberOwner": false,
      "isUserInCountry": false
    },
    "ownerLikelihood": {
      "isOwner": false,
      "likelihood": "LOW"
    },
    "overview": {
      "name": "Saptami, India",
      "detailId": 8010527,
      "geo": "Mumbai, India",
      "geoId": 304554,
      "isOwner": false,
      "links": {
        "warUrl": "/UserReviewEdit-g304554-d8010527-Saptami-Mumbai_Maharashtra.html",
        "addPhotoUrl": "/PostPhotos-g304554-d8010527",
        "ownerAddPhotoUrl": "/ManagePhotos-d8010527-Saptami"
      },
      "location": {
        "latitude": 19.103235,
        "longitude": 72.88693,
        "directionsUrl": "U09sX2h0dHBzOi8vbWFwcy5nb29nbGUuY29tL21hcHM/c2FkZHI9JmRhZGRyPUhvbGlkYXkrSW5uK0hvdGVsJTJDK0xvYmJ5K0xldmVsJTJDK1Nha2krTmFrYStKdW5jdGlvbiUyQytBbmRoZXJpK0t1cmxhK1JvYWQlMkMrQW5kaGVyaStFYXN0JTJDK011bWJhaSs0MDAwNzIrSW5kaWFAMTkuMTAzMjM1LDcyLjg4NjkzX1NUNw==",
        "landmark": "<b>2.1 miles</b> from Powai Lake",
        "neighborhood": "Eastern Suburbs"
      },
      "contact": {
        "address": "Holiday Inn Hotel, Lobby Level, Saki Naka Junction, Andheri Kurla Road, Andheri East, Mumbai 400072 India",
        "email": "saptami@himia.in",
        "phone": null,
        "website": "djR0X2h0dHA6Ly93d3cuaG9saWRheWlubi5jb20vaG90ZWxzL3VzL2VuL211bWJhaS9ib21hcC9ob3RlbGRldGFpbC9kaW5pbmdfM1dK"
      },
      "rating": {
        "primaryRanking": {
          "rank": 2,
          "totalCount": 8574,
          "category": "Restaurants",
          "geo": "Mumbai",
          "url": "/Restaurants-g304554-Mumbai_Maharashtra.html"
        },
        "secondaryRanking": null,
        "primaryRating": 5,
        "reviewCount": 720,
        "ratingQuestions": [
          {
            "name": "Food",
            "rating": 45,
            "icon": "restaurants"
          },
          {
            "name": "Service",
            "rating": 40,
            "icon": "bell"
          },
          {
            "name": "Value",
            "rating": 40,
            "icon": "wallet-fill"
          },
          {
            "name": "Atmosphere",
            "rating": 40,
            "icon": "ambience"
          }
        ]
      },
      "award": {
        "icon": "travelers-choice-badge",
        "awardText": "Travelers' Choice",
        "yearsText": "",
        "isTravelersChoice": false
      },
      "tags": {
        "reviewSnippetSections": null
      },
      "detailCard": {
        "tagTexts": {
          "priceRange": {
            "tagCategoryId": 240,
            "tags": [
              {
                "tagId": 10954,
                "tagValue": "Fine Dining"
              }
            ]
          },
          "cuisines": {
            "tagCategoryId": 231,
            "tags": [
              {
                "tagId": 10346,
                "tagValue": "Indian"
              },
              {
                "tagId": 10659,
                "tagValue": "Asian"
              },
              {
                "tagId": 10679,
                "tagValue": "Healthy"
              },
              {
                "tagId": 10648,
                "tagValue": "International"
              }
            ]
          },
          "dietaryRestrictions": {
            "tagCategoryId": 285,
            "tags": [
              {
                "tagId": 10665,
                "tagValue": "Vegetarian Friendly"
              },
              {
                "tagId": 10697,
                "tagValue": "Vegan Options"
              },
              {
                "tagId": 10751,
                "tagValue": "Halal"
              },
              {
                "tagId": 10992,
                "tagValue": "Gluten Free Options"
              }
            ]
          },
          "meals": {
            "tagCategoryId": 233,
            "tags": [
              {
                "tagId": 10597,
                "tagValue": "Breakfast"
              },
              {
                "tagId": 10598,
                "tagValue": "Lunch"
              },
              {
                "tagId": 10599,
                "tagValue": "Dinner"
              },
              {
                "tagId": 10606,
                "tagValue": "Brunch"
              },
              {
                "tagId": 10704,
                "tagValue": "Late Night"
              },
              {
                "tagId": 10949,
                "tagValue": "Drinks"
              }
            ]
          },
          "features": {
            "tagCategoryId": 234,
            "tags": [
              {
                "tagId": 10601,
                "tagValue": "Takeout"
              },
              {
                "tagId": 10602,
                "tagValue": "Reservations"
              },
              {
                "tagId": 10702,
                "tagValue": "Private Dining"
              },
              {
                "tagId": 10852,
                "tagValue": "Seating"
              },
              {
                "tagId": 10854,
                "tagValue": "Parking Available"
              },
              {
                "tagId": 10856,
                "tagValue": "Validated Parking"
              },
              {
                "tagId": 10857,
                "tagValue": "Valet Parking"
              },
              {
                "tagId": 10860,
                "tagValue": "Highchairs Available"
              },
              {
                "tagId": 10861,
                "tagValue": "Wheelchair Accessible"
              },
              {
                "tagId": 10862,
                "tagValue": "Serves Alcohol"
              },
              {
                "tagId": 10863,
                "tagValue": "Full Bar"
              },
              {
                "tagId": 16547,
                "tagValue": "Table Service"
              },
              {
                "tagId": 10612,
                "tagValue": "Buffet"
              },
              {
                "tagId": 10864,
                "tagValue": "Wine and Beer"
              },
              {
                "tagId": 20992,
                "tagValue": "Drive Thru"
              },
              {
                "tagId": 21271,
                "tagValue": "Family style"
              }
            ]
          },
          "establishmentType": {
            "tagCategoryId": 230,
            "tags": [
              {
                "tagId": 10591,
                "tagValue": "Restaurants"
              }
            ]
          }
        },
        "numericalPrice": "$15 - $24",
        "improveListingUrl": "/ImproveListing-d8010527.html",
        "updateListingUrl": "/ManageListing-g304554-d8010527-Saptami-Mumbai_Maharashtra.html",
        "restaurantOwner": {
          "text": null,
          "tooltip": null,
          "trackingItemName": ""
        }
      }
    }
  }
}

        """
        return await self._make_request("GET", "/restaurant/getRestaurantDetailsV2", params={"restaurantsId": restaurant_id, "currency": currency})

    async def get_supported_currencies(self):
        """
        Retrieves a list of currencies supported by the API asynchronously.

        Returns:
            dict: A list of supported currencies.
        """
        return await self._make_request("GET", "/getCurrency")

async def main():
    """Main async function to run example usage."""
    try:
        # Initialize the client
        client = TripAdvisorAPIClient()

        # --- Example Usage ---

        # Search for hotels in New York
        print("--- Searching for Hotels in New York ---")
        hotels = await client.search_hotels_by_city("New York")
        if hotels:
            print(f"Found {len(hotels)} hotels.")
            # Get details for the first hotel
            first_hotel_id = hotels[0].get("id")
            if first_hotel_id:
                print(f"\n--- Getting Details for Hotel ID: {first_hotel_id} ---")
                hotel_details = await client.get_hotel_details(first_hotel_id)
                if hotel_details:
                    print(f"Hotel Name: {hotel_details.get('data', {}).get('name', 'N/A')}")
        print("-" * 30)

        # To avoid hitting rate limits on the free tier of RapidAPI
        print("Waiting for 30 seconds before next API call...")
        await asyncio.sleep(30)

        # Search for restaurants in Paris
        print("--- Searching for Restaurants in Paris ---")
        restaurants = await client.search_restaurants_by_city("Paris")
        if restaurants:
            print(f"Found {len(restaurants)} restaurants.")
            # Get details for the first restaurant
            first_restaurant_id = restaurants[0].get("id")
            if first_restaurant_id:
                print(f"\n--- Getting Details for Restaurant ID: {first_restaurant_id} ---")
                restaurant_details = await client.get_restaurant_details(first_restaurant_id)
                if restaurant_details:
                     print(f"Restaurant Name: {restaurant_details.get('data', {}).get('name', 'N/A')}")
        print("-" * 30)

    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
