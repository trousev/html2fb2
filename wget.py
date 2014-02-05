import urllib2
import os
import md5

class Wget:


    __cache_folder__ = os.path.join(os.getenv("HOME"), ".pywget.cache")
    try: os.makedirs(__cache_folder__)
    except: pass
    __opener__ = None

    @staticmethod
    def cache_folder():
        return Wget.__cache_folder__

    @staticmethod
    def __opener():
        if Wget.__opener__ == None:
            Wget.__opener__ = urllib2.build_opener()
            Wget.__opener__.addheaders = [('User-agent', 'Mozilla/5.0')]
        return Wget.__opener__

    @staticmethod
    def __md5(line):
        m = md5.new()
        m.update(line)
        return m.hexdigest()

    @staticmethod
    def get(url):
        cache_file = os.path.join(Wget.cache_folder(), Wget.__md5(url))
        try:
            f = open(cache_file,'r')
            ans = f.read()
            f.close()
        except IOError:
            response = Wget.__opener().open(url)
            ans = response.read()
            f = open(cache_file,'w')
            f.write(ans)
            f.close()
        except SocketError:
            print "WAAAAAGH"
        return ans
