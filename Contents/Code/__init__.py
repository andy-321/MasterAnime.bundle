
######################################################################################
#                                                                                    #
#	                                MasterAnime                                      #
#                                                                                    #
######################################################################################

TITLE = "MasterAnime"
PREFIX = "/video/masteranime"
BASE_URL = "http://www.masterani.me"
ICON_COVER = "icon-cover.png"

MAIN_ART                    = 'icon-cover.png'
MAIN_ICON                   = 'icon-cover.png'

CATEGORIES = {'Recent Anime': '/api/releases',
              'Being Watched': '/api/anime/trending/now',
              'Trending Now': '/api/anime/trending/today'}

network = SharedCodeService.networking
StringFromURL = network.StringFromURL
#from networking import StringFromURL



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
            key=Callback(CategoryMenu, title = title, url = url), title=title
            )
        )
    oc.add(InputDirectoryObject(
        key=Callback(Search), title='Search', prompt='Search...'
        ))

    return oc

####################################################################################################

@route(PREFIX + "/categorymenu")
def CategoryMenu(title, url):
    oc = ObjectContainer(title1=title)
    Log.Debug('CategoryMenu')

    showString = StringFromURL(BASE_URL+url)
    shows = JSON.ObjectFromString(showString)
    #shows = JSON.ObjectFromURL(BASE_URL+url)
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
            thumb = Resource.ContentsOfURLWithFallback(url = 'http://cdn.masterani.me/poster/{poster}'.format(poster=showPoster), fallback='icon-cover.png')#,
        ))

    return oc


####################################################################################################


@route(PREFIX + "/TVShow")
def TVShowMenu(title, UrlID):
    oc = ObjectContainer(title1=title)

    Log.Debug(UrlID)
    Log.Debug(BASE_URL+'/api/anime/{id}/detailed'.format(id=UrlID))

    showString = StringFromURL(BASE_URL+'/api/anime/{id}/detailed'.format(id=UrlID))
    show = JSON.ObjectFromString(showString)
    #show = JSON.ObjectFromURL(BASE_URL+'/api/anime/{id}/detailed'.format(id=UrlID))
    Log.Debug('TVShow Menu')
    oc.add(TVShowObject(
        key = Callback(EpisodeMenu, title = title, UrlID=UrlID),
        rating_key = show.get('info').get('score'),
        title = show.get('info').get('title'),
        summary = show.get('info').get('synopsis'),
        genres = [genre.get('name') for genre in show.get('genres')],
        thumb = Resource.ContentsOfURLWithFallback(url = 'http://cdn.masterani.me/poster/{poster}'.format(poster=show.get('poster')), fallback='icon-cover.png'),
        episode_count = len(show.get('episodes')),
        rating = float(show.get('info').get('score'))*2 if show.get('info').get('score') is not None else None,
        duration = int(show.get('info').get('episode_length')) * 60000 if show.get('info').get('episode_length') is not None else None,
        content_rating  = show.get('info').get('age_rating')
    ))
    ytTrailer = show.get('info').get('youtube_trailer_id')
    if(ytTrailer is not None and Prefs['showTrailer']):
        oc.add(EpisodeObject(
            title='Trailer: ' + title,
            url='http://www.youtube.com/watch?v={id}'.format(id=ytTrailer),
            thumb = R("trailer-cover.png")
        ))
    if(show.get('franchise_count') > 0):
        franchiseString = StringFromURL(BASE_URL+'/api/anime/{id}/franchise'.format(id=UrlID))
        franchise = JSON.ObjectFromString(franchiseString)
        #franchise = JSON.ObjectFromURL(BASE_URL+'/api/anime/{id}/franchise'.format(id=UrlID))
        oc.add(DirectoryObject(
            key = Callback(CategoryMenu,title="Franchise: " + title, url='/api/anime/{id}/franchise'.format(id=UrlID)),
            title = 'Franchise: ' + title,
            thumb = Resource.ContentsOfURLWithFallback(url = 'http://cdn.masterani.me/poster/{poster}'.format(poster=franchise[0].get('anime').get('poster').get('file')), fallback='icon-cover.png')#,
        ))

    recommendedString = StringFromURL(BASE_URL+'/api/anime/{id}/recommendations'.format(id=UrlID))
    recommended = JSON.ObjectFromString(recommendedString)
    #recommended = JSON.ObjectFromURL(BASE_URL+'/api/anime/{id}/recommendations'.format(id=UrlID))
    if (recommended):
        oc.add(DirectoryObject(
            key = Callback(CategoryMenu,title="Recommended: " + title, url='/api/anime/{id}/recommendations'.format(id=UrlID)),
            title = 'Recommended: ' + title,
            thumb = Resource.ContentsOfURLWithFallback(url = 'http://cdn.masterani.me/poster/{poster}'.format(poster=recommended[0].get('recommended').get('poster').get('file')), fallback='icon-cover.png')#,
        ))

    return oc

####################################################################################################


@route(PREFIX + "/EpisodeMenu")
def EpisodeMenu(title, UrlID):
    oc = ObjectContainer(title1=title)

    showString = StringFromURL(BASE_URL+'/api/anime/{id}/detailed'.format(id=UrlID))
    show = JSON.ObjectFromString(showString)
    #show = JSON.ObjectFromURL(BASE_URL+'/api/anime/{id}/detailed'.format(id=UrlID))
    episodes = show.get('episodes')
    pageSize = 30

    if len(episodes) < pageSize:
        for episode in episodes:#TODO: Try to split into pages
            info = episode.get('info')
            oc.add(EpisodeObject(
                title = info.get('title'),
                show = title,
                duration = int(info.get('duration')) * 60000 if info.get('duration') is not None else None,
                originally_available_at = Datetime.ParseDate(info.get('aired')) if info.get('aired') is not None else None,
                summary = info.get('description'),
                index = int(info.get('episode')) if info.get('episode') is not None else None,
                thumb = Resource.ContentsOfURLWithFallback(url = 'http://cdn.masterani.me/episodes/{thumb}'.format(thumb=episode.get('thumbnail')), fallback='icon-cover.png'),
                url= BASE_URL+'/anime/watch/{slug}/{episode}'.format(slug = show.get('info').get('slug'), episode = info.get('episode'))
            ))
    else:
        pageEpisodes = [episodes[x:x + pageSize] for x in xrange(0, len(episodes), pageSize)]
        for pageNum, page in enumerate(pageEpisodes, 1):
            Log.Debug(page)
            oc.add(DirectoryObject(
                key = Callback(PagedEpisodeMenu,title=title + "page: " + str(pageNum), episodes = page, show = show),
                title = 'Page: ' + str(pageNum),
                thumb = Resource.ContentsOfURLWithFallback(url='http://cdn.masterani.me/poster/{poster}'.format(poster=show.get('poster')), fallback='icon-cover.png')#,
            )
        )


    return oc

####################################################################################################


#@route(PREFIX + "/PagedEpisodeMenu")
def PagedEpisodeMenu(title, episodes,show):
    oc = ObjectContainer(title1=title)
    Log.Debug(type(episodes))
    Log.Debug(episodes)
    for episode in episodes:
        info = episode.get('info')
        oc.add(EpisodeObject(
            title=info.get('title'),
            show=title,
            duration=int(info.get('duration')) * 60000 if info.get('duration') is not None else None,
            originally_available_at=Datetime.ParseDate(info.get('aired')) if info.get('aired') is not None else None,
            summary=info.get('description'),
            index=int(info.get('episode')) if info.get('episode') is not None else None,
            thumb=Resource.ContentsOfURLWithFallback(
                url='http://cdn.masterani.me/episodes/{thumb}'.format(thumb=episode.get('thumbnail')),
                fallback='icon-cover.png'),
            url=BASE_URL + '/anime/watch/{slug}/{episode}'.format(slug=show.get('info').get('slug'),
                                                                  episode=info.get('episode'))
        ))

    return oc

####################################################################################################


@route(PREFIX + "/search")
def Search(query, page = 1):
    if len(query) > 30:
        Log.Error('Search query of length={length} is too long. Must be less than 30 characters'.format(length = len(query)))
        return ObjectContainer(header='Error', message='The search can not be greater than 30 characters.')
    oc = ObjectContainer(title1 = query)
    try:

        resultsString = StringFromURL(BASE_URL + '/api/anime/filter?search={query}&order=score_desc&page={page}'.format(query = query, page = page))
        results = JSON.ObjectFromString(resultsString)
        #results = JSON.ObjectFromURL(BASE_URL + '/api/anime/filter?search={query}&order=score_desc&page={page}'.format(query = query, page = page), cacheTime = CACHE_1MINUTE)
    except:
        Log.Error('No search results found for {query}.'.format(query = query))
        return ObjectContainer(header='Error', message='No search results found')
    for show in results.get('data'):
        showTitle = show.get('title')
        id = show.get('id')
        showPoster = show.get('poster').get('file')
        oc.add(DirectoryObject(
            key = Callback(TVShowMenu, title=showTitle, UrlID=id),
            title = showTitle,
            thumb = Resource.ContentsOfURLWithFallback(url = 'http://cdn.masterani.me/poster/{poster}'.format(poster=showPoster), fallback='icon-cover.png')#,
        ))
    if int(page) < int(results.get('last_page')):
        oc.add(DirectoryObject(
            key = Callback(Search, query = query, page = int(page)+1),
            title = 'Next Page'
        ))

    return oc
