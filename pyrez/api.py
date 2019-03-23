import configparser
from datetime import timedelta, datetime
from hashlib import md5 as getMD5Hash
from json.decoder import JSONDecodeError as JSONException
import os
from sys import version_info as pythonVersion

import requests_async as requests

import pyrez
from pyrez.enumerations import *
from pyrez.exceptions import *
from pyrez.http import HttpRequest as HttpRequest
from pyrez.models import *

class BaseAPI:
    """
    DON'T INITALISE THIS YOURSELF!

    Attributes:
        _devId [int]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
        _authKey [str]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
        _endpointBaseURL [str]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
        _responseFormat [str]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
        _header [str]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
    Methods:
        __init__(devId, authKey, endpoint, responseFormat=pyrez.enumerations.ResponseFormat.JSON, header=None)
        _encode(string, encodeType="utf-8")
        _httpRequest(url, header=None)
        _saveConfigIni(sessionId)
        _readConfigIni()
    """
    def __init__(self, devId, authKey, endpoint, responseFormat=ResponseFormat.JSON, header=None):
        """
        The constructor for BaseAPI class.

        Keyword arguments/Parameters:
            devId [int]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            authKey [str]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            endpoint [str]: The endpoint that will be used by default for outgoing requests.
            responseFormat [pyrez.enumerations.ResponseFormat]: The response format that will be used by default when making requests (default pyrez.enumerations.ResponseFormat.JSON)
            header: 
        """
        if devId is None or authKey is None:
            raise IdOrAuthEmptyException("DevId or AuthKey not specified!")
        elif len(str(devId)) != 4 or not str(devId).isnumeric():
            raise InvalidArgumentException("You need to pass a valid DevId!")
        elif len(str(authKey)) != 32 or not str(authKey).isalnum():
            raise InvalidArgumentException("You need to pass a valid AuthKey!")
        elif endpoint is None:
            raise InvalidArgumentException("Endpoint can't be empty!")
        self._devId = int(devId)
        self._authKey = str(authKey)
        self._endpointBaseURL = str(endpoint)
        self._responseFormat = ResponseFormat(responseFormat) if isinstance(responseFormat, ResponseFormat) else ResponseFormat.JSON
        self._header = header

    def __getConfigIniFile(self):
        conf = configparser.ConfigParser()
        conf.read("{0}/conf.ini".format(os.path.dirname(os.path.abspath(__file__))))
        return conf
    
    def _saveConfigIni(self, sessionId):
        conf = self.__getConfigIniFile()
        conf["Session"]["SessionId"] = sessionId
        with open("{0}/conf.ini".format(os.path.dirname(os.path.abspath(__file__))), 'w') as configfile:
            conf.write(configfile)

    def _readConfigIni(self):
        conf = self.__getConfigIniFile()
        return conf["Session"]["SessionId"] if conf["Session"]["SessionId"] else None

    def _encode(self, string, encodeType="utf-8"):
        """
        Keyword arguments/Parameters:
            string [str]: 
            encodeType [str]: 
        Returns:
            String encoded to format type
        """
        return str(string).encode(encodeType)

    async def _httpRequest(self, url, header=None):
        httpResponse = await HttpRequest(header if header else self._header).get(url)
        if httpResponse.status >= 400:
            raise NotFoundException("Wrong URL: {0}".format(httpResponse.text()))
        result = await httpResponse.json() if httpResponse.json() is not None else httpResponse.text()
        print(result)
        return await result

class HiRezAPI(BaseAPI):
    """
    Class for handling connections and requests to Hi-Rez Studios APIs. IS BETTER DON'T INITALISE THIS YOURSELF!
    """

    PYREZ_HEADER = { "User-Agent": "{0} [Python/{1.major}.{1.minor} requests/{2}]".format(pyrez.__title__, pythonVersion, requests.__version__) }

    def __init__(self, devId, authKey, endpoint, responseFormat=ResponseFormat.JSON, sessionId=None, useConfigIni=False):
        """
        The constructor for HiRezAPI class.

        Keyword arguments/Parameters:
            devId [int]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            authKey [str]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            endpoint [str]: The endpoint that will be used by default for outgoing requests.
            responseFormat [pyrez.enumerations.ResponseFormat]: The response format that will be used by default when making requests (default pyrez.enumerations.ResponseFormat.JSON)
            sessionId [str]: An active sessionId (default None)
            useConfigIni [bool]: (default False)
        """
        super().__init__(devId, authKey, endpoint, responseFormat, self.PYREZ_HEADER)
        self.useConfigIni = useConfigIni
        if self.useConfigIni:
            self.currentSessionId = self._readConfigIni()
        else:
            self.currentSessionId = sessionId if sessionId is not None and str(sessionId).isalnum() and self.testSession(sessionId) else None

    def _createTimeStamp(self, frmt="%Y%m%d%H%M%S"):
        """
        Keyword arguments/Parameters:
            frmt [str]: Format of timeStamp
        Returns:
            Returns the current time formatted
        """
        return self._getCurrentTime().strftime(frmt)

    def _getCurrentTime(self):
        """        
        Returns:
            Returns the current UTC time
        """
        return datetime.utcnow()

    def _createSignature(self, method, timestamp=None):
        """
        Keyword arguments/Parameters:
            method [str]: Method name
            timestamp [str]: Format of timeStamp
        Returns:
            Returns a Signature hash of the method
        """
        return getMD5Hash(self._encode("{0}{1}{2}{3}".format(self._devId, method.lower(), self._authKey, timestamp if timestamp is not None else self._createTimeStamp()))).hexdigest()

    def _sessionExpired(self):
        return self.currentSessionId is None or not str(self.currentSessionId).isalnum()

    def _buildUrlRequest(self, apiMethod=None, params=()): # [queue, date, hour]
        if apiMethod is None:
            raise InvalidArgumentException("No API method specified!")
        urlRequest = "{0}/{1}{2}".format(self._endpointBaseURL, apiMethod.lower(), self._responseFormat)
        if apiMethod.lower() != "ping":
            urlRequest += "/{0}/{1}".format(self._devId, self._createSignature(apiMethod.lower()))
            if self.currentSessionId is not None and apiMethod.lower() != "createsession":
                if apiMethod.lower() == "testsession":
                    return urlRequest + "/{0}/{1}".format(str(params[0]), self._createTimeStamp())
                urlRequest += "/{0}".format(self.currentSessionId)
            urlRequest += "/{0}".format(self._createTimeStamp())
            for param in params:
                if param is not None:
                    urlRequest += "/{0}".format(param.strftime("yyyyMMdd") if isinstance(param, datetime) else str(param.value) if isinstance(param, (IntFlag, Enum)) else str(param))
        return urlRequest.replace(' ', "%20")
    
    async def makeRequest(self, apiMethod=None, params=()):
        if apiMethod is None:
            raise InvalidArgumentException("No API method specified!")
        elif(apiMethod.lower() != "createsession" and self._sessionExpired()):
            self._createSession()
        result = await self._httpRequest(apiMethod if str(apiMethod).lower().startswith("http") else self._buildUrlRequest(apiMethod, params))
        if result:
            if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
                return result
            if str(result).lower().find("ret_msg") == -1:
                return None if len(str(result)) == 2 and str(result) == "[]" else result
            hasError = APIResponse(**result) if str(result).startswith('{') else APIResponse(**result[0])
            if hasError is not None and hasError.hasRetMsg():
                if hasError.retMsg == "Approved":
                    self.currentSessionId = Session(**result).sessionId
                    if self.useConfigIni:
                        self._saveConfigIni(self.currentSessionId)
                elif hasError.retMsg.find("dailylimit") != -1:
                    raise DailyLimitException("Daily limit reached: " + hasError.retMsg)
                elif hasError.retMsg.find("Maximum number of active sessions reached") != -1:
                    raise SessionLimitException("Concurrent sessions limit reached: " + hasError.retMsg)
                elif hasError.retMsg.find("Invalid session id") != -1:
                    self._createSession()
                    return self.makeRequest(apiMethod, params)
                elif hasError.retMsg.find("Exception while validating developer access") != -1:
                    raise WrongCredentials("Wrong credentials: " + hasError.retMsg)
                elif hasError.retMsg.find("No match_queue returned.  It is likely that the match wasn't live when GetMatchPlayerDetails() was called") != -1:
                    raise GetMatchPlayerDetailsException("Match isn't live: " + hasError.retMsg)
                elif hasError.retMsg.find("Only training queues") != -1 and hasError.retMsg.find("are supported for GetMatchPlayerDetails()") != -1:
                    raise GetMatchPlayerDetailsException("Queue not supported by getMatchPlayerDetails(): " + hasError.retMsg)
                elif hasError.retMsg.find("The server encountered an error processing the request") != -1:
                    raise RequestErrorException("The server encountered an error processing the request: " + hasError.retMsg)
                elif hasError.retMsg.find("404") != -1:
                    raise NotFoundException("Not found: " + hasError.retMsg)
            return result

    def switchEndpoint(self, endpoint):
        if not isinstance(endpoint, Endpoint):
            raise InvalidArgumentException("You need to use the Endpoint enum to switch endpoints")
        self._endpointBaseURL = str(endpoint)

    async def _createSession(self):
        """
        /createsession[ResponseFormat]/{devId}/{signature}/{timestamp}
        A required step to Authenticate the devId/signature for further API use.
        """
        try:
            tempResponseFormat, self._responseFormat = self._responseFormat, ResponseFormat.JSON
            responseJSON = await self.makeRequest("createsession")
            self._responseFormat = tempResponseFormat
            return Session(**responseJSON) if responseJSON is not None else None
        except WrongCredentials as x:
            raise x
    
    async def ping(self):
        """
        /ping[ResponseFormat]
        A quick way of validating access to the Hi-Rez API.
        
        Returns:
            Object of pyrez.models.Ping: Returns the infos about the API.
        """
        tempResponseFormat, self._responseFormat = self._responseFormat, ResponseFormat.JSON
        responseJSON = await self.makeRequest("ping")
        self._responseFormat = tempResponseFormat
        return Ping(responseJSON) if responseJSON is not None else None
    
    async def testSession(self, sessionId=None):
        """
        /testsession[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}
        A means of validating that a session is established.

        Keyword arguments/Parameters:
            sessionId [str]: 
        Returns:
            Object of pyrez.models.TestSession
        """
        session = self.currentSessionId if sessionId is None or not str(sessionId).isalnum() else sessionId
        uri = "{0}/testsession{1}/{2}/{3}/{4}/{5}".format(self._endpointBaseURL, self._responseFormat, self._devId, self._createSignature("testsession"), session, self._createTimeStamp())
        result = await self._httpRequest(uri)
        return result.find("successful test") != -1

    async def getDataUsed(self):
        """
        /getdataused[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}
        Returns API Developer daily usage limits and the current status against those limits.
        
        Returns:
            Object of pyrez.models.DataUsed
        """
        tempResponseFormat, self._responseFormat = self._responseFormat, ResponseFormat.JSON
        responseJSON = await self.makeRequest("getdataused")
        self._responseFormat = tempResponseFormat
        return None if responseJSON is None else DataUsed(**responseJSON) if str(responseJSON).startswith('{') else DataUsed(**responseJSON[0])
    
    async def getHiRezServerFeeds(self):
        req = await self._httpRequest("http://status.hirezstudios.com/history.atom", self._header)
        #https://hirezstudios.statuspage.io/history.rss
        #https://hirezstudios.statuspage.io/history.json
        return req
    
    async def getHiRezServerStatus(self):
        """
        /gethirezserverstatus[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}
        Function returns UP/DOWN status for the primary game/platform environments. Data is cached once a minute.
        
        Returns:
            Object of pyrez.models.HiRezServerStatus
        """
        tempResponseFormat, self._responseFormat = self._responseFormat, ResponseFormat.JSON
        responseJSON = await self.makeRequest("gethirezserverstatus")
        self._responseFormat = tempResponseFormat
        if responseJSON is None:
            return None
        servers = []
        for server in responseJSON:
            obj = HiRezServerStatus(**server)
            servers.append(obj)
        return servers if servers else None
        
    async def getPatchInfo(self):
        """
        /getpatchinfo[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}
        Function returns information about current deployed patch. Currently, this information only includes patch version.
        
        Returns:
            Object of pyrez.models.PatchInfo
        """
        tempResponseFormat, self._responseFormat = self._responseFormat, ResponseFormat.JSON
        responseJSON = await self.makeRequest("getpatchinfo")
        self._responseFormat = tempResponseFormat
        return PatchInfo(**responseJSON) if responseJSON is not None else None
    
    async def getFriends(self, playerId):
        """
        /getfriends[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{playerId}
        Returns the User names of each of the player’s friends of one player. [PC only]
        
        Returns:
            List of pyrez.models.Friend objects
        """
        if playerId is None or not str(playerId).isnumeric():
            raise InvalidArgumentException("Invalid player: playerId must to be numeric (int)!")
        responseJSON = await self.makeRequest("getfriends", [playerId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return responseJSON
        if responseJSON is None:
            return None
        friends = []
        for friend in responseJSON:
            obj = Friend(**friend)
            friends.append(obj)
        return friends if friends else None

    async def getMatchDetails(self, matchId):
        """
        /getmatchdetails[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{matchId}
        Returns the statistics for a particular completed match.
        
        Keyword arguments/Parameters:
            matchId [int]: 
        """
        if matchId is None or not str(matchId).isnumeric():
            raise InvalidArgumentException("Invalid Match ID: matchId must to be numeric (int)!")
        responseJSON = await self.makeRequest("getmatchdetails", [matchId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return responseJSON
        if responseJSON is None:
            return None
        matchDetails = []
        for matchDetail in responseJSON:
            obj = MatchDetail(**matchDetail)
            matchDetails.append(obj)
        return matchDetails if matchDetails else None
    
    async def getMatchDetailsBatch(self, matchIds=()):
        """
        /getmatchdetailsbatch[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{matchId,matchId,matchId,...matchId}
        Returns the statistics for a particular set of completed matches.

        Keyword arguments/Parameters:
            matchIds [list]: 
        NOTE:
            There is a byte limit to the amount of data returned;
            Please limit the CSV parameter to 5 to 10 matches because of this and for Hi-Rez DB Performance reasons.
        """
        responseJSON = await self.makeRequest("getmatchdetailsbatch", [','.join(matchIds)])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return responseJSON
        if responseJSON is None:
            return None
        matchDetails = []
        for matchDetail in responseJSON:
            obj = MatchDetail(**matchDetail)
            matchDetails.append(obj)
        return matchDetails if matchDetails else None

    async def getMatchHistory(self, playerId):
        """
        /getmatchhistory[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{playerId}
        Gets recent matches and high level match statistics for a particular player.

        Keyword arguments/Parameters:
            playerId [int]: 
        """
        if playerId is None or not str(playerId).isnumeric():
            raise InvalidArgumentException("Invalid player: playerId must to be numeric (int)!")
        getMatchHistoryResponse = await self.makeRequest("getmatchhistory", [playerId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getMatchHistoryResponse
        if getMatchHistoryResponse is None:
            return None
        matchHistorys = []
        for matchHistory in getMatchHistoryResponse:
            obj = MatchHistory(**matchHistory)
            matchHistorys.append(obj)
        return matchHistorys if matchHistorys else None

    async def getMatchIdsByQueue(self, queueId, date, hour=-1):
        """
        /getmatchidsbyqueue[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{queue}/{date}/{hour}
        Lists all Match IDs for a particular Match Queue; useful for API developers interested in constructing data by Queue.
        To limit the data returned, an {hour} parameter was added (valid values: 0 - 23).
        An {hour} parameter of -1 represents the entire day, but be warned that this may be more data than we can return for certain queues.
        Also, a returned “active_flag” means that there is no match information/stats for the corresponding match.
        Usually due to a match being in-progress, though there could be other reasons.

        Keyword arguments/Parameters:
            queueId [int]: 
            date [int]: 
            hour [int]: 
        NOTE:
            To avoid HTTP timeouts in the GetMatchIdsByQueue() method, you can now specify a 10-minute window within the specified {hour} field to lessen the size of data returned by appending a “,mm” value to the end of {hour}.
            For example, to get the match Ids for the first 10 minutes of hour 3, you would specify {hour} as “3,00”.
            This would only return the Ids between the time 3:00 to 3:09.
            Rules below:
                Only valid values for mm are “00”, “10”, “20”, “30”, “40”, “50”
                To get the entire third hour worth of Match Ids, call GetMatchIdsByQueue() 6 times, specifying the following values for {hour}: “3,00”, “3,10”, “3,20”, “3,30”, “3,40”, “3,50”.
                The standard, full hour format of {hour} = “hh” is still supported.
        """
        if queueId is None or not str(queueId).isnumeric() or not isinstance(queueId, (RealmRoyaleQueue, SmiteQueue, PaladinsQueue)):
            raise InvalidArgumentException("Invalid Queue ID: queueId must to be numeric (int)!")
        getMatchIdsByQueueResponse = await self.makeRequest("getmatchidsbyqueue", [queueId, date.strftime("%Y%m%d") if isinstance(date, datetime) else date, hour])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getMatchIdsByQueueResponse
        if getMatchIdsByQueueResponse is None:
            return None
        queueIds = []
        for i in getMatchIdsByQueueResponse:
            obj = MatchIdByQueue(**i)
            queueIds.append(obj)
        return queueIds if queueIds else None

    async def getPlayer(self, player, portalId=None):
        """
        /getplayer[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{player}
        /getplayer[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{player}/{portalId}
        Returns league and other high level data for a particular player.

        Keyword arguments/Parameters:
            player [int] or [str]: 
        """
        if player is None or len(str(player)) <= 3:
            raise InvalidArgumentException("Invalid player: playerId must to be numeric (int)!")
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return await self.makeRequest("getplayer", [player, portalId] if portalId else [player])
        if isinstance(self, RealmRoyaleAPI):
            plat = "hirez" if not str(player).isdigit() or str(player).isdigit() and len(str(player)) <= 8 else "steam"
            return PlayerRealmRoyale(**self.makeRequest("getplayer", [player, plat]))
        res = await self.makeRequest("getplayer", [player, portalId] if portalId else [player])
        return None if res is None else PlayerSmite(**res[0]) if isinstance(self, SmiteAPI) else PlayerPaladins(**res[0])

    async def getPlayerAchievements(self, playerId):
        """
        /getplayerachievements[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{playerId}
        Returns select achievement totals (Double kills, Tower Kills, First Bloods, etc) for the specified playerId.

        Keyword arguments/Parameters:
            playerId [int]:
        """
        if playerId is None or not str(playerId).isnumeric():
            raise InvalidArgumentException("Invalid player: playerId must to be numeric (int)!")
        getPlayerAchievementsResponse = await self.makeRequest("getplayerachievements", [playerId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getPlayerAchievementsResponse
        if getPlayerAchievementsResponse is None:
            return None
        return PlayerAcheviements(**getPlayerAchievementsResponse) if str(getPlayerAchievementsResponse).startswith('{') else PlayerAcheviements(**getPlayerAchievementsResponse[0])

    async def getPlayerIdByName(self, playerName):
        """
        /getplayeridbyname[ResponseFormat]/{developerId}/{signature}/{session}/{timestamp}/{playerName}
        Function returns a list of Hi-Rez playerId values (expected list size = 1) for playerName provided. The playerId returned is
        expected to be used in various other endpoints to represent the player/individual regardless of platform.

        Keyword arguments/Parameters:
            playerName [str]: 
        """
        getPlayerIdByNameResponse = await self.makeRequest("getplayeridbyname", [playerName])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getPlayerIdByNameResponse
        if getPlayerIdByNameResponse is None:
            return None
        playerIds = []
        for i in getPlayerIdByNameResponse:
            obj = PlayerIdByX(**i)
            playerIds.append(obj)
        return playerIds if playerIds else None

    async def getPlayerIdByPortalUserId(self, portalId, portalUserId):
        """
        /getplayeridbyportaluserid[ResponseFormat]/{developerId}/{signature}/{session}/{timestamp}/{portalId}/{portalUserId}
        Function returns a list of Hi-Rez playerId values (expected list size = 1) for {portalId}/{portalUserId} combination provided.
        The playerId returned is expected to be used in various other endpoints to represent the player/individual regardless of platform.

        Keyword arguments/Parameters:
            portalId [int]: 
            portalUserId [int]: 
        """
        getPlayerIdByPortalUserIdResponse = await self.makeRequest("getplayeridbyportaluserid", [portalId, portalUserId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getPlayerIdByPortalUserIdResponse
        if getPlayerIdByPortalUserIdResponse is None:
            return None
        playerIds = []
        for i in getPlayerIdByPortalUserIdResponse:
            obj = PlayerIdByX(**i)
            playerIds.append(obj)
        return playerIds if playerIds else None

    async def getPlayerIdsByGamerTag(self, gamerTag, portalId):
        """
        /getplayeridsbygamertag[ResponseFormat]/{developerId}/{signature}/{session}/{timestamp}/{portalId}/{gamerTag}
        Function returns a list of Hi-Rez playerId values for {portalId}/{portalUserId} combination provided. The appropriate
        playerId extracted from this list by the API end user is expected to be used in various other endpoints to represent the player/individual regardless of platform.

        Keyword arguments/Parameters:
            gamerTag [str]: 
        """
        getPlayerIdsByGamerTagResponse = await self.makeRequest("getplayeridsbygamertag", [portalId, gamerTag])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getPlayerIdsByGamerTagResponse
        if getPlayerIdsByGamerTagResponse is None:
            return None
        playerIds = []
        for i in getPlayerIdsByGamerTagResponse:
            obj = PlayerIdByX(**i)
            playerIds.append(obj)
        return playerIds if playerIds else None

    async def getPlayerStatus(self, playerId):
        """
        /getplayerstatus[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{playerId}
        Returns player status as follows:
            0 - Offline, 1 - In Lobby, 2 - god Selection, 3 - In Game, 4 - Online, 5 - Player not found

        Keyword arguments/Parameters:
            playerId [int]: 
        
        Returns:
            Object of pyrez.models.PlayerStatus
        """
        if playerId is None or not str(playerId).isnumeric():
            raise InvalidArgumentException("Invalid player: playerId must to be numeric (int)!")
        getPlayerStatusResponse = await self.makeRequest("getplayerstatus", [playerId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getPlayerStatusResponse
        if not getPlayerStatusResponse:
            return None
        return PlayerStatus(**getPlayerStatusResponse) if str(getPlayerStatusResponse).startswith('{') else PlayerStatus(**getPlayerStatusResponse[0]) if getPlayerStatusResponse else None

    async def getQueueStats(self, playerId, queueId):
        """
        /getqueuestats[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{playerId}/{queue}
        Returns match summary statistics for a (player, queue) combination grouped by gods played.

        Keyword arguments/Parameters:
            playerId [int]:
            queueId [int]: 
        """
        if playerId is None or not str(playerId).isnumeric():
            raise InvalidArgumentException("Invalid player: playerId must to be numeric (int)!")
        #elif queueId is None or not str(queueId).isnumeric() or not isinstance(queueId, (RealmRoyaleQueue, SmiteQueue, PaladinsQueue)):
        #    raise InvalidArgumentException("Invalid Queue ID: queueId must to be numeric (int)!")
        getQueueStatsResponse = await self.makeRequest("getqueuestats", [playerId, queueId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getQueueStatsResponse
        if not getQueueStatsResponse:
            return None
        queueStatsList = []
        for i in getQueueStatsResponse:
            obj = QueueStats(**i)
            queueStatsList.append(obj)
        return queueStatsList if queueStatsList else None

class BaseSmitePaladinsAPI(HiRezAPI):
    """
    Class for handling connections and requests to Hi-Rez Studios APIs. IS BETTER DON'T INITALISE THIS YOURSELF!
    """
    def __init__(self, devId, authKey, endpoint, responseFormat=ResponseFormat.JSON, sessionId=None, useConfigIni=True):
        """
        The constructor for BaseSmitePaladinsAPI class.

        Keyword arguments/Parameters:
            devId [int]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            authKey [str]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            endpoint [str]: The endpoint that will be used by default for outgoing requests.
            responseFormat [pyrez.enumerations.ResponseFormat]: The response format that will be used by default when making requests (default pyrez.enumerations.ResponseFormat.JSON)
            sessionId [str]: An active sessionId (default None)
            useConfigIni [bool]: (default True)
        """
        super().__init__(devId, authKey, endpoint, responseFormat, sessionId, useConfigIni)

    async def getDemoDetails(self, matchId):
        """
        /getdemodetails[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{matchId}
        Returns information regarding a particular match.  Rarely used in lieu of getmatchdetails().
        
        Keyword arguments/Parameters:
            matchId [int]: 
        """
        if not isinstance(self, (PaladinsAPI, SmiteAPI)):
            raise NotSupported("This method is just for Paladins and Smite API's!")
        elif matchId is None or not str(matchId).isnumeric():
            raise InvalidArgumentException("Invalid Match ID: matchId must to be numeric (int)!")
        getDemoDetailsResponse = await self.makeRequest("getdemodetails", [matchId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getDemoDetailsResponse
        if not getDemoDetailsResponse:
            return None
        demoDetails = []
        for demoDetail in getDemoDetailsResponse:
            obj = SmiteDemoDetail(**demoDetail) if isinstance(self, SmiteAPI) else PaladinsDemoDetail(**demoDetail)
            demoDetails.append(obj)
        return demoDetails if demoDetails else None

    async def getEsportsProLeagueDetails(self):
        """
        /getesportsproleaguedetails[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}
        Returns the matchup information for each matchup for the current eSports Pro League season.
        An important return value is “match_status” which represents a match being scheduled (1), in-progress (2), or complete (3)
        """
        if not isinstance(self, (PaladinsAPI, SmiteAPI)):
            raise NotSupported("This method is just for Paladins and Smite API's!")
        getEsportsProLeagueDetailsResponse = await self.makeRequest("getesportsproleaguedetails")
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getEsportsProLeagueDetailsResponse
        if not getEsportsProLeagueDetailsResponse:
            return None
        details = []
        for detail in getEsportsProLeagueDetailsResponse:
            obj = EsportProLeagueDetail(**detail)
            details.append(obj)
        return details if details else None

    async def getGods(self, languageCode=LanguageCode.English):
        """
        /getgods[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{languageCode}
        Returns all Gods and their various attributes.
        
        Keyword arguments/Parameters:
            languageCode [int] or [pyrez.enumerations.LanguageCode]: (default pyrez.enumerations.LanguageCode.English)
        Returns:
            List of pyrez.models.God or pyrez.models.Champion objects
        """
        if not isinstance(self, (PaladinsAPI, SmiteAPI)):
            raise NotSupported("This method is just for Paladins and Smite API's!")
        getGodsResponse = await self.makeRequest("getgods", [languageCode])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getGodsResponse
        if not getGodsResponse:
            return None
        gods = []
        for i in getGodsResponse:
            obj = God(**i) if isinstance(self, SmiteAPI) else Champion(**i)
            gods.append(obj)
        return gods if gods else None

    async def getGodLeaderboard(self, godId, queueId):
        """
        /getgodleaderboard[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{godId}/{queue}
        Returns the current season’s leaderboard for a god/queue combination. [SmiteAPI only; queues 440, 450, 451 only]
        
        Keyword arguments/Parameters:
            godId [int]: 
            queueId [int]: 
        """
        if godId is None or not str(godId).isnumeric() or not isinstance(godId, (Gods, Champions)):
            raise InvalidArgumentException("Invalid God ID: godId must to be numeric (int)!")
        elif queueId is None or not str(queueId).isnumeric() or not isinstance(queueId, (SmiteQueue, PaladinsQueue)):
            raise InvalidArgumentException("Invalid Queue ID: queueId must to be numeric (int)!")
        getGodLeaderboardResponse = await self.makeRequest("getgodleaderboard", [godId, queueId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getGodLeaderboardResponse
        if not getGodLeaderboardResponse:
            return None
        godLeaderb = []
        for leader in getGodLeaderboardResponse:
            obj = GodLeaderboard(**leader) if isinstance(self, SmiteAPI) else ChampionLeaderboard(**i)
            godLeaderb.append(obj)
        return godLeaderb if godLeaderb else None
    
    async def getGodRanks(self, playerId):
        """
        /getgodranks[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{playerId}
        Returns the Rank and Worshippers value for each God a player has played.
        
        Keyword arguments/Parameters:
            playerId [int]: 
        Returns:
            List of pyrez.models.GodRank objects
        """
        if not isinstance(self, (PaladinsAPI, SmiteAPI)):
            raise NotSupported("This method is just for Paladins and Smite API's!")
        if playerId is None or not str(playerId).isnumeric():
            raise InvalidArgumentException("Invalid player: playerId must to be numeric (int)!")
        getGodRanksResponse = await self.makeRequest("getgodranks", [playerId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getGodRanksResponse
        if not getGodRanksResponse:
            return None
        godRanks = []
        for i in getGodRanksResponse:
            godRanks.append(GodRank(**i))
        return godRanks if godRanks else None

    async def getGodSkins(self, godId, languageCode=LanguageCode.English):
        """
        /getgodskins[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{godId}/{languageCode}
        Returns all available skins for a particular God.
        
        Keyword arguments/Parameters:
            godId [int]: 
            languageCode [int] or [pyrez.enumerations.LanguageCode]: (default pyrez.enumerations.LanguageCode.English)
        """
        if godId is None or not str(godId).isnumeric() or not isinstance(godId, (Gods, Champions)):
            raise InvalidArgumentException("Invalid Queue ID: queueId must to be numeric (int)!")
        getGodSkinsResponse = await self.makeRequest("getgodskins", [godId, languageCode])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getGodSkinsResponse
        if getGodSkinsResponse is None:
            return None
        godSkins = []
        for godSkin in getGodSkinsResponse:
            obj = GodSkin(**godSkin) if isinstance(self, SmiteAPI) != -1 else ChampionSkin(**godSkin)
            godSkins.append(obj)
        return godSkins if godSkins else None

    async def getItems(self, languageCode=LanguageCode.English):
        """
        /getitems[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{languageCode}
        Returns all Items and their various attributes.
        
        Keyword arguments/Parameters:
            languageCode [int] or [pyrez.enumerations.LanguageCode]: (default pyrez.enumerations.LanguageCode.English)
        """
        getItemsResponse = await self.makeRequest("getitems", [languageCode])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getItemsResponse
        if not getItemsResponse:
            return None
        items = []
        for item in getItemsResponse:
            obj = SmiteItem(**item) if isinstance(self, SmiteAPI) != -1 else PaladinsItem(**item)
            items.append(obj)
        return items if items else None

    async def getLeagueLeaderboard(self, queueId, tier, split):
        """
        /getleagueleaderboard[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{queue}/{tier}/{split}
        Returns the top players for a particular league (as indicated by the queue/tier/split parameters).

        Keyword arguments/Parameters:
            queueId [int]: 
            tier [int]: 
            split [int]: 
        """
        if queueId is None or not str(queueId).isnumeric() or not isinstance(queueId, (SmiteQueue, PaladinsQueue)):
            raise InvalidArgumentException("Invalid Queue ID: queueId must to be numeric (int)!")
        getLeagueLeaderboardResponse = await self.makeRequest("getleagueleaderboard", [queueId, tier, split])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getLeagueLeaderboardResponse
        if not getLeagueLeaderboardResponse:
            return None
        leagueLeaderboards = []
        for leaderboard in getLeagueLeaderboardResponse:
            obj = LeagueLeaderboard(**leaderboard)
            leagueLeaderboards.append(obj)
        return leagueLeaderboards if leagueLeaderboards else None
        
    async def getLeagueSeasons(self, queueId):
        """
        /getleagueseasons[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{queueId}
        Provides a list of seasons (including the single active season) for a match queue.

        Keyword arguments/Parameters:
            queueId [int]
        """
        if queueId is None or not str(queueId).isnumeric() or not isinstance(queueId, (SmiteQueue, PaladinsQueue)):
            raise InvalidArgumentException("Invalid Queue ID: queueId must to be numeric (int)!")
        getLeagueSeasonsResponse = await self.makeRequest("getleagueseasons", [queueId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getLeagueSeasonsResponse
        if not getLeagueSeasonsResponse:
            return None
        seasons = []
        for season in getLeagueSeasonsResponse:
            obj = LeagueSeason(**season)
            items.append(obj)
        return seasons if seasons else None

    async def getMatchPlayerDetails(self, matchId):
        """
        /getmatchplayerdetails[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{matchId}
        Returns player information for a live match.

        Keyword arguments/Parameters:
            matchId [int]: 
        """
        if matchId is None or not str(matchId).isnumeric():
            raise InvalidArgumentException("Invalid Match ID: matchId must to be numeric (int)!")
        responseJSON = await self.makeRequest("getmatchplayerdetails", [matchId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return responseJSON
        if responseJSON is None:
            return None
        players = []
        for player in responseJSON:
            obj = MatchPlayerDetail(**player)
            players.append(obj)
        return players if players else None

class PaladinsAPI(BaseSmitePaladinsAPI):
    """
    Class for handling connections and requests to Paladins API.
    """
    def __init__(self, devId, authKey, responseFormat=ResponseFormat.JSON, sessionId=None, useConfigIni=True):
        """
        The constructor for PaladinsAPI class.

        Keyword arguments/Parameters:
            devId [int]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            authKey [str]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            responseFormat [pyrez.enumerations.ResponseFormat]: The response format that will be used by default when making requests (default pyrez.enumerations.ResponseFormat.JSON)
            sessionId [str]: An active sessionId (default None)
            useConfigIni [bool]: (default True)
        """
        super().__init__(devId, authKey, Endpoint.PALADINS, responseFormat, sessionId, useConfigIni)

    async def getLatestPatchNotes(self, languageCode=LanguageCode.English):
        getLatestUpdateNotesResponse = await self.makeRequest("https://cms.paladins.com/wp-json/api/get-posts/{0}?tag=update-notes".format(languageCode.value if isinstance(languageCode, LanguageCode) else languageCode))
        if getLatestUpdateNotesResponse is None:
            return None
        post = PaladinsWebsitePost(**getLatestUpdateNotesResponse[0])
        getLatestPatchNotesResponse = await self.makeRequest("https://cms.paladins.com/wp-json/api/get-post/{0}?slug={1}".format(languageCode.value if isinstance(languageCode, LanguageCode) else languageCode, post.slug))
        return PaladinsWebsitePost(**getLatestPatchNotesResponse) if getLatestPatchNotesResponse is not None else None
    async def getPaladinsWebsitePostBySlug(self, slug, languageCode=LanguageCode.English):
        getPaladinsWebsitePostsResponse = await self.makeRequest("https://cms.paladins.com/wp-json/api/get-post/{0}?slug={1}".format(languageCode.value if isinstance(languageCode, LanguageCode) else languageCode, slug))
        if getPaladinsWebsitePostsResponse is None:
            return None
        posts = []
        for post in getPaladinsWebsitePostsResponse:
            obj = PaladinsWebsitePost(**post)
            posts.append(obj)
        return posts if posts else None
    async def getPaladinsWebsitePosts(self, languageCode=LanguageCode.English):
        getPaladinsWebsitePostsResponse = await self.makeRequest("https://cms.paladins.com/wp-json/api/get-posts/{0}".format(languageCode.value if isinstance(languageCode, LanguageCode) else languageCode))
        if getPaladinsWebsitePostsResponse is None:
            return None
        posts = []
        for post in getPaladinsWebsitePostsResponse:
            obj = PaladinsWebsitePost(**post)
            posts.append(obj)
        return posts if posts else None
    async def getPaladinsWebsitePostsByQuery(self, query, languageCode=LanguageCode.English):
        getPaladinsWebsitePostsResponse = await self.makeRequest("https://cms.paladins.com/wp-json/api/get-posts/{0}?search={1}".format(languageCode.value if isinstance(languageCode, LanguageCode) else languageCode, query))
        if getPaladinsWebsitePostsResponse is None:
            return None
        posts = []
        for post in getPaladinsWebsitePostsResponse:
            obj = PaladinsWebsitePost(**post)
            posts.append(obj)
        return posts if posts else None
    
    async def getChampions(self, languageCode=LanguageCode.English):
        """
        /getchampions[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{languageCode}
        Returns all Champions and their various attributes. [PaladinsAPI only]

        Keyword arguments/Parameters:
            languageCode [int] or [pyrez.enumerations.LanguageCode]: (default pyrez.enumerations.LanguageCode.English)
        """
        getChampionsResponse = await self.makeRequest("getchampions", [languageCode]) # self.makeRequest("getgods", languageCode)
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getChampionsResponse
        if getChampionsResponse is None:
            return None
        champions = []
        for i in getChampionsResponse:
            obj = Champion(**i)
            champions.append(obj)
        return champions if champions else None

    async def getChampionsCards(self, godId, languageCode=LanguageCode.English):
        """
        /getchampioncards[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{godId}/{languageCode}
        Returns all Champion cards. [PaladinsAPI only]

        Keyword arguments/Parameters:
            languageCode [int] or [pyrez.enumerations.LanguageCode]: (default pyrez.enumerations.LanguageCode.English)
        """
        if godId is None or not str(godId).isnumeric() or not isinstance(godId, Champions):
            raise InvalidArgumentException("Invalid Queue ID: queueId must to be numeric (int)!")
        getChampionsCardsResponse = await self.makeRequest("getchampioncards", [godId, languageCode])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getChampionsCardsResponse
        if getChampionsCardsResponse is None:
            return None
        cards = []
        for i in getChampionsCardsResponse:
            obj = ChampionCard(**i)
            cards.append(obj)
        return cards if cards else None

    async def getChampionLeaderboard(self, godId, queueId=PaladinsQueue.Live_Competitive_Keyboard):
        """
        /getchampionleaderboard[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{godId}/{queueId}
        Returns the current season’s leaderboard for a champion/queue combination. [PaladinsAPI; only queue 428]
        
        Keyword arguments/Parameters:
            godId [int]: 
            queueId [int]: 
        """
        if godId is None or not str(godId).isnumeric() or not isinstance(godId, Champions):
            raise InvalidArgumentException("Invalid Queue ID: queueId must to be numeric (int)!")
        getChampionLeaderboardResponse = await self.makeRequest("getchampionleaderboard", [godId, queueId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getChampionLeaderboardResponse
        if getChampionLeaderboardResponse is None:
            return None
        getChampionLeaderboard = []
        for i in getChampionLeaderboardResponse:
            obj = ChampionLeaderboard(**i)
            getChampionLeaderboard.append(obj)
        return getChampionLeaderboard if getChampionLeaderboard else None

    async def getChampionRanks(self, playerId):
        """
        /getchampionranks[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{playerId}
        Returns the Rank and Worshippers value for each Champion a player has played. [PaladinsAPI only]
        
        Keyword arguments/Parameters:
            playerId [int]: 
        """
        if playerId is None or not str(playerId).isnumeric():
            raise InvalidArgumentException("Invalid player: playerId must to be numeric (int)!")
        getChampionsRanksResponse = await self.makeRequest("getgodranks", [playerId]) # self.makeRequest("getchampionranks", [playerId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getChampionsRanksResponse
        if getChampionsRanksResponse is None:
            return None
        championRanks = []
        for i in getChampionsRanksResponse:
            championRanks.append(GodRank(**i))
        return championRanks if championRanks else None

    async def getChampionRecommendedItems(self, godId, languageCode=LanguageCode.English):
        """
        /getchampionrecommendeditems[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{godId}/{languageCode}
        Returns the Recommended Items for a particular Champion. [PaladinsAPI only]

        WARNING: OSBSOLETE - NO DATA RETURNED

        Keyword arguments/Parameters:
            godId [int]: 
            languageCode [int] or [pyrez.enumerations.LanguageCode]: (default pyrez.enumerations.LanguageCode.English)
        """
        if godId is None or not str(godId).isnumeric() or not isinstance(godId, Champions):
            raise InvalidArgumentException("Invalid Queue ID: queueId must to be numeric (int)!")
        raise DeprecatedException("OSBSOLETE - NO DATA RETURNED")
        return await self.makeRequest("getchampionrecommendeditems", [godId, languageCode])
        
    async def getChampionSkins(self, godId, languageCode=LanguageCode.English):
        """
        /getchampionskins[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{godId}/{languageCode}
        Returns all available skins for a particular Champion. [PaladinsAPI only]
        
        Keyword arguments/Parameters:
            godId : int
            languageCode [int] or [pyrez.enumerations.LanguageCode]: (default pyrez.enumerations.LanguageCode.English)
        """
        if godId is None or not str(godId).isnumeric() or not isinstance(godId, Champions):
            raise InvalidArgumentException("Invalid Queue ID: queueId must to be numeric (int)!")
        getChampSkinsResponse = await self.makeRequest("getchampionskins", [godId, languageCode])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getChampSkinsResponse
        if getChampSkinsResponse is None:
            return None
        champSkins = []
        for champSkin in getChampSkinsResponse:
            obj = ChampionSkin(**champSkin)
            champSkins.append(obj)
        return champSkins if champSkins else None

    async def getPlayerIdInfoForXboxAndSwitch(self, playerName):
        """
        /getplayeridinfoforxboxandswitch[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{playerName}
        Meaningful only for the Paladins Xbox API. Paladins Xbox data and Paladins Switch data is stored in the same DB.
        Therefore a Paladins Gamer Tag value could be the same as a Paladins Switch Gamer Tag value.
        Additionally, there could be multiple identical Paladins Switch Gamer Tag values.
        The purpose of this method is to return all Player ID data associated with the playerName (gamer tag) parameter.
        The expectation is that the unique player_id returned could then be used in subsequent method calls. [PaladinsAPI only]
        """
        getPlayerIdInfoForXboxAndSwitchResponse = await self.makeRequest("getplayeridinfoforxboxandswitch", [playerName])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getPlayerIdInfoForXboxAndSwitchResponse
        if getPlayerIdInfoForXboxAndSwitchResponse is None:
            return None
        playerIds = []
        for playerId in getPlayerIdInfoForXboxAndSwitchResponse:
            obj = PlayerIdInfoForXboxOrSwitch(**playerId)
            playerIds.append(obj)
        return playerIds if playerIds else None

    async def getPlayerLoadouts(self, playerId, languageCode=LanguageCode.English):
        """
        /getplayerloadouts[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/playerId}/{languageCode}
        Returns deck loadouts per Champion. [PaladinsAPI only]
        
        Keyword arguments/Parameters:
            playerId [int]: 
            languageCode [int] or [pyrez.enumerations.LanguageCode]: (default pyrez.enumerations.LanguageCode.English)
        """
        if playerId is None or not str(playerId).isnumeric():
            raise InvalidArgumentException("Invalid player: playerId must to be numeric (int)!")
        getPlayerLoadoutsResponse = await self.makeRequest("getplayerloadouts", [playerId, languageCode])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getPlayerLoadoutsResponse
        if getPlayerLoadoutsResponse is None:
            return None
        playerLoadouts = []
        for playerLoadout in getPlayerLoadoutsResponse:
            obj = PlayerLoadout(**playerLoadout)
            playerLoadouts.append(obj)
        return playerLoadouts if playerLoadouts else None
        
class RealmRoyaleAPI(HiRezAPI):
    """
    Class for handling connections and requests to Realm Royale API.
    """
    def __init__(self, devId, authKey, responseFormat=ResponseFormat.JSON, sessionId=None, useConfigIni=True):
        """
        The constructor for RealmRoyaleAPI class.

        Keyword arguments/Parameters:
            devId [int]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            authKey [str]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            endpoint [str]: The endpoint that will be used by default for outgoing requests.
            responseFormat [pyrez.enumerations.ResponseFormat]: The response format that will be used by default when making requests (default pyrez.enumerations.ResponseFormat.JSON)
            sessionId [str]: An active sessionId (default None)
            useConfigIni [bool]: (default True)
        """
        super().__init__(devId, authKey, Endpoint.REALM_ROYALE, responseFormat, sessionId, useConfigIni)

    async def getLeaderboard(self, queueId, rankingCriteria):
        """
        /getleaderboard[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{queueId}/{ranking_criteria}

        - for duo and quad queues/modes the individual's placement results reflect their team/grouping; solo is self-explanatory
        - will limit results to the top 500 players (minimum 50 matches played per queue); we never like to expose weak/beginner players
        - players that select to be "private" will have their player_name and player_id values hidden
        - {ranking_criteria} can be: 1: team_wins, 2: team_average_placement (shown below), 3: individual_average_kills, 4. win_rate, possibly/probably others as desired
        - expect this data to be cached on an hourly basis because the query to acquire the data will be expensive; don't spam the calls
        """
        if queueId is None or not str(queueId).isnumeric() or not isinstance(queueId, RealmRoyaleQueue):
            raise InvalidArgumentException("Invalid Queue ID: queueId must to be numeric (int)!")
        getLeaderboardResponse = await self.makeRequest("getleaderboard", [queueId, rankingCriteria])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getLeaderboardResponse
        return RealmRoyaleLeaderboard(**getLeaderboardResponse) if getLeaderboardResponse is not None else None

    async def getPlayerMatchHistory(self, playerId):
        """
        /getplayermatchhistory[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{playerId}
        """
        if playerId is None or not str(playerId).isnumeric():
            raise InvalidArgumentException("Invalid player: playerId must to be numeric (int)!")
        getPlayerMatchHistoryResponse = await self.makeRequest("getplayermatchhistory", [playerId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getPlayerMatchHistoryResponse
        return RealmMatchHistory(**getPlayerMatchHistoryResponse) if getPlayerMatchHistoryResponse is not None else None

    async def getPlayerMatchHistoryAfterDatetime(self, playerId, startDatetime):
        """
        /getplayermatchhistoryafterdatetime[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{playerId}/{startDatetime}
        """
        if playerId is None or not str(playerId).isnumeric():
            raise InvalidArgumentException("Invalid player: playerId must to be numeric (int)!")
        getPlayerMatchHistoryAfterDatetimeResponse = await self.makeRequest("getplayermatchhistoryafterdatetime", [playerId, startDatetime.strftime("yyyyMMddHHmmss") if isinstance(startDatetime, datetime) else startDatetime])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getPlayerMatchHistoryAfterDatetimeResponse
        return RealmMatchHistory(**getPlayerMatchHistoryAfterDatetimeResponse) if getPlayerMatchHistoryAfterDatetimeResponse is not None else None

    async def getPlayerStats(self, playerId):
        """ 
        /getplayerstats[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{playerId}
        """
        if playerId is None or not str(playerId).isnumeric():
            raise InvalidArgumentException("Invalid player: playerId must to be numeric (int)!")
        return await self.makeRequest("getplayerstats", [playerId])

    async def getTalents(self, languageCode=LanguageCode.English):
        """
        /gettalents[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{langId}
        Get all talents
        """
        if languageCode is None or not str(languageCode).isnumeric() or not isinstance(language, LanguageCode):
            raise InvalidArgumentException("Invalid LangId!")
        responseJSON = await self.makeRequest("gettalents", [languageCode])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return responseJSON
        if responseJSON is None:
            return None
        talents = []
        for talent in responseJSON:
            obj = RealmRoyaleTalent(**talent)
            talents.append(obj)
        return talents if talents else None

    async def searchPlayers(self, playerName):
        """
        /searchplayers[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{playerName}
        """
        searchPlayerResponse = await self.makeRequest("searchplayers", [playerName])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return searchPlayerResponse
        if searchPlayerResponse is None:
            return None
        players = []
        for player in searchPlayerResponse:
            obj = Player(**player)
            players.append(obj)
        return players if players else None

class SmiteAPI(BaseSmitePaladinsAPI):
    """
    Class for handling connections and requests to Smite API.
    """
    def __init__(self, devId, authKey, responseFormat=ResponseFormat.JSON, sessionId=None, useConfigIni=True):
        """
        The constructor for SmiteAPI class.

        Keyword arguments/Parameters:
            devId [int]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            authKey [str]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            responseFormat [pyrez.enumerations.ResponseFormat]: The response format that will be used by default when making requests (default pyrez.enumerations.ResponseFormat.JSON)
            sessionId [str]: An active sessionId (default None)
            useConfigIni [bool]: (default True)
        """
        super().__init__(devId, authKey, Endpoint.SMITE, responseFormat, sessionId, useConfigIni)

    async def getGodRecommendedItems(self, godId, languageCode=LanguageCode.English):
        """
        /getgodrecommendeditems[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{godId}/{languageCode}
        Returns the Recommended Items for a particular God. [SmiteAPI only]
        
        Keyword arguments/Parameters:
            godId [int]: 
            languageCode [int] or [pyrez.enumerations.LanguageCode]: (default pyrez.enumerations.LanguageCode.English)
        """
        getGodRecommendedItemsResponse = await self.makeRequest("getgodrecommendeditems", [godId, languageCode])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getGodRecommendedItemsResponse
        if getGodRecommendedItemsResponse is None:
            return None
        recommendedItems = []
        for recommendedItem in getGodRecommendedItemsResponse:
            obj = GodRecommendedItem(**recommendedItem)
            recommendedItems.append(obj)
        return recommendedItems if recommendedItems else None

    async def getMotd(self):
        """
        /getmotd[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}
        Returns information about the 20 most recent Match-of-the-Days.
        """
        getMOTDResponse = await self.makeRequest("getmotd")
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getMOTDResponse
        if getMOTDResponse is None:
            return None
        motds = []
        for motd in getMOTDResponse:
            obj = MOTD(**motd)
            motds.append(obj)
        return motds if motds else None

    async def getTeamDetails(self, clanId):
        """
        /getteamdetails[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{clanId}
        Lists the number of players and other high level details for a particular clan.
        
        Keyword arguments/Parameters:
            clanId [int]: 
        """
        if clanId is None or not str(clanId).isnumeric():
            raise InvalidArgumentException("Invalid Clan ID: clanId must to be numeric (int)!")
        getTeamDetailsResponse = await self.makeRequest("getteamdetails", [clanId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getTeamDetailsResponse
        if getTeamDetailsResponse is None:
            return None
        teamDetails = []
        for teamDetail in getTeamDetailsResponse:
            obj = TeamDetail(**teamDetail)
            teamDetails.append(obj)
        return teamDetails if teamDetails else None
    
    async def getTeamMatchHistory(self, clanId):
        """
        /getteammatchhistory[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{clanId}
        Gets recent matches and high level match statistics for a particular clan/team.
        
        WARNING: DEPRECATED - NO DATA RETURNED
        """
        raise DeprecatedException("*DEPRECATED* - As of 2.14 Patch, /getteammatchhistory is no longer supported and will return a NULL dataset.")
        if clanId is None or not str(clanId).isnumeric():
            raise InvalidArgumentException("Invalid Clan ID: clanId must to be numeric (int)!")
        return await self.makeRequest("getteammatchhistory", [clanId])

    async def getTeamPlayers(self, clanId):
        """
        /getteamplayers[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{clanId}
        Lists the players for a particular clan.
        
        Keyword arguments/Parameters:
            clanId [int]: 
        """
        if clanId is None or not str(clanId).isnumeric():
            raise InvalidArgumentException("Invalid Clan ID: clanId must to be numeric (int)!")
        getTeamPlayers = await self.makeRequest("getteamplayers", [clanId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getTeamPlayers
        if getTeamPlayers is None:
            return None
        teamPlayers = []
        for teamPlayer in getTeamPlayers:
            obj = TeamPlayer(**teamPlayer)
            teamPlayers.append(obj)
        return teamPlayers if teamPlayers else None

    async def getTopMatches(self):
        """
        /gettopmatches[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}
        Lists the 50 most watched / most recent recorded matches.
        """
        getTopMatchesResponse = await self.makeRequest("gettopmatches")
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getTopMatchesResponse
        if getTopMatchesResponse is None:
            return None
        matches = []
        for match in getTopMatchesResponse:
            obj = SmiteTopMatch(**match)
            matches.append(obj)
        return matches if matches else None
    async def searchTeams(self, teamId):
        """
        /searchteams[ResponseFormat]/{devId}/{signature}/{session}/{timestamp}/{searchTeam}
        Returns high level information for Clan names containing the “searchTeam” string. [SmiteAPI only]
        
        Keyword arguments/Parameters:
            teamId [int]: 
        """
        getSearchTeamsResponse = await self.makeRequest("searchteams", [teamId])
        if str(self._responseFormat).lower() == str(ResponseFormat.XML).lower():
            return getSearchTeamsResponse
        if getSearchTeamsResponse is None:
            return None
        teams = []
        for team in getSearchTeamsResponse:
            obj = TeamSearch(**team)
            teams.append(obj)
        return teams if teams else None

class HandOfTheGodsAPI(HiRezAPI):
    """
    Class for handling connections and requests to Hand of the Gods API.
    """
    def __init__(self, devId, authKey, responseFormat=ResponseFormat.JSON, sessionId=None, useConfigIni=True):
        """
        The constructor for SmiteAPI class.

        Keyword arguments/Parameters:
            devId [int]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            authKey [str]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            responseFormat [pyrez.enumerations.ResponseFormat]: The response format that will be used by default when making requests (default pyrez.enumerations.ResponseFormat.JSON)
            sessionId [str]: An active sessionId (default None)
            useConfigIni [bool]: (default True)
        """
        raise NotSupported("Not released yet!")
        super().__init__(devId, authKey, Endpoint.HAND_OF_THE_GODS, responseFormat, sessionId, useConfigIni)

class PaladinsStrikeAPI(HiRezAPI):
    """
    Class for handling connections and requests to Paladins Strike API.
    """
    def __init__(self, devId, authKey, responseFormat=ResponseFormat.JSON, sessionId=None, useConfigIni=True):
        """
        The constructor for PaladinsStrikeAPI class.

        Keyword arguments/Parameters:
            devId [int]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            authKey [str]: Used for authentication. This is the developer ID that you receive from Hi-Rez Studios.
            responseFormat [pyrez.enumerations.ResponseFormat]: The response format that will be used by default when making requests (default pyrez.enumerations.ResponseFormat.JSON)
            sessionId [str]: An active sessionId (default None)
            useConfigIni [bool]: (default True)
        """
        raise NotSupported("Not released yet!")
        super().__init__(devId, authKey, Endpoint.PALADINS_STRIKE, responseFormat, sessionId, useConfigIni)
