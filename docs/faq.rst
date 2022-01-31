Frequently Asked Questions
==========================

*This document is WIP*

Error Messages
--------------
*requests.exceptions.ConnectionError: ('Connection aborted.', ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None))*
Issue: This sometimes happens during the first download of data when the pressure on the API is high and lots of data are being collected over a longer period of time. 
Solution: Restart the program with the same parameters. The program is designed in a way that the downloaded data is constantly written to disk so that the next time, only the difference needs to be downloaded.

