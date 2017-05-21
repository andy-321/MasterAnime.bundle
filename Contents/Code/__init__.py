
######################################################################################
#                                                                                    #
#	                                MasterAnime                                      #
#                                                                                    #
######################################################################################

TITLE = "MasterAnime"
PREFIX = "/video/masteranime"
BASE_URL = "https://www.masterani.me"
ICON_COVER = "icon-cover.png"

MAIN_ART                    = 'icon-cover.png'
MAIN_ICON                   = 'icon-cover.png'

CATEGORIES = {'Recent Anime': '/api/releases',
              'Being Watched': '/api/anime/trending/now',
              'Trending Now':'/api/anime/trending/today'}

####################################################################################################
def Start():
    ObjectContainer.title1 = TITLE


    DirectoryObject.thumb = R(ICON_COVER)

#    HTTP.CacheTime = CACHE_1HOUR
    HTTP.CacheTime = None
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36'


####################################################################################################
@handler(PREFIX, TITLE, MAIN_ICON, MAIN_ART)
def MainMenu():
    oc = ObjectContainer(title1=TITLE)
    Log.Debug('MainMenu')
    for (title, url) in CATEGORIES.items():
        Log.Debug(title + ', ' + url)
        oc.add(DirectoryObject(
            key=Callback(CategoryMenu, title = title, url = url), title=title,
            )
        )
        shows = JSON.ObjectFromURL(BASE_URL + url)
        anime = shows[0].get('anime')

    return oc

####################################################################################################

@route(PREFIX + "/categorymenu")
def CategoryMenu(title, url):
    oc = ObjectContainer(title1=title)
    Log.Debug('CategoryMenu')
    shows = JSON.ObjectFromURL(BASE_URL+url)
    Log.Debug(shows)
    recommended = False
    for show in shows:
        if (Regex('\/recommendations$').search(url)):
            anime = show.get('recommended')
            recommended = True
        else:
            anime = show.get('anime')
        if (anime is None):
            showTitle = show.get('title')
            showPoster = show.get('poster')
            slug = show.get('slug')
            id = Regex('^\d+(?=-)').search(slug).group()
        else:
            showTitle = anime.get('title')
            showPoster = anime.get('poster')
            if(Regex('\/franchise$').search(url) or recommended):
                showPoster = showPoster.get('file')
            id = anime.get('id')
        oc.add(DirectoryObject(
            key = Callback(TVShowMenu,title=showTitle, UrlID=id),
            title = showTitle,
            thumb = Resource.ContentsOfURLWithFallback(url = 'https://cdn.masterani.me/poster/{poster}'.format(poster=showPoster), fallback='icon-cover.png')#,
        ))

    return oc


####################################################################################################


@route(PREFIX + "/TVShow")
def TVShowMenu(title, UrlID):
    oc = ObjectContainer(title1=title)

    Log.Debug(UrlID)
    Log.Debug(BASE_URL+'/api/anime/{id}/detailed'.format(id=UrlID))

    show = JSON.ObjectFromURL(BASE_URL+'/api/anime/{id}/detailed'.format(id=UrlID))
    Log.Debug('TVShow Menu')
    oc.add(TVShowObject(
        key = Callback(EpisodeMenu, title = title, UrlID=UrlID),
        rating_key = show.get('info').get('score'),
        title = show.get('info').get('title'),
        summary = show.get('info').get('synopsis'),
        genres = [genre.get('name') for genre in show.get('genres')],
        thumb = Resource.ContentsOfURLWithFallback(url = 'https://cdn.masterani.me/poster/{poster}'.format(poster=show.get('poster')), fallback='icon-cover.png'),
        episode_count = len(show.get('episodes')),
        rating = float(show.get('info').get('score'))*2 if show.get('info').get('score') is not None else None,
        duration = int(show.get('info').get('episode_length')) * 60000 if show.get('info').get('episode_length') is not None else None,
        content_rating  = show.get('info').get('age_rating')
    ))
    if(show.get('franchise_count') > 0):
        franchise = JSON.ObjectFromURL(BASE_URL+'/api/anime/{id}/franchise'.format(id=UrlID))
        oc.add(DirectoryObject(
            key = Callback(CategoryMenu,title="Franchise: " + title, url='/api/anime/{id}/franchise'.format(id=UrlID)),
            title = 'Franchise: ' + title,
            thumb = Resource.ContentsOfURLWithFallback(url = 'https://cdn.masterani.me/poster/{poster}'.format(poster=franchise[0].get('anime').get('poster').get('file')), fallback='icon-cover.png')#,
        ))
    recommended = JSON.ObjectFromURL(BASE_URL+'/api/anime/{id}/recommendations'.format(id=UrlID))
    if (recommended):
        oc.add(DirectoryObject(
            key = Callback(CategoryMenu,title="Recommended: " + title, url='/api/anime/{id}/recommendations'.format(id=UrlID)),
            title = 'Recommended: ' + title,
            thumb = Resource.ContentsOfURLWithFallback(url = 'https://cdn.masterani.me/poster/{poster}'.format(poster=recommended[0].get('recommended').get('poster').get('file')), fallback='icon-cover.png')#,
        ))

    return oc

####################################################################################################


@route(PREFIX + "/EpisodeMenu")
def EpisodeMenu(title, UrlID):
    oc = ObjectContainer(title1=title)

    show = JSON.ObjectFromURL(BASE_URL+'/api/anime/{id}/detailed'.format(id=UrlID))
    episodes = show.get('episodes')

    for episode in episodes:
        info = episode.get('info')
        oc.add(EpisodeObject(
            title = info.get('title'),
            show = title,
            duration = int(info.get('duration')) * 60000 if info.get('duration') is not None else None,
            originally_available_at = Datetime.ParseDate(info.get('aired')) if info.get('aired') is not None else None,
            summary = info.get('description'),
            index = int(info.get('episode')) if info.get('episode') is not None else None,
            thumb = Resource.ContentsOfURLWithFallback(url = 'https://cdn.masterani.me/episodes/{thumb}'.format(thumb=episode.get('thumbnail')), fallback='icon-cover.png'),
            url= BASE_URL+'/anime/watch/{slug}/{episode}'.format(slug = show.get('info').get('slug'), episode = info.get('episode'))
        ))

    return oc