global suite 

suite = { 
'ADCS': ['test_ADCS.py', 'test_PingService.py', 'test_ResetService.py'], 
'EPS': ['test_EPS.py', 'test_PingService.py', 'test_ResetService.py']
}
    
def isTest(system, test):
    global suite

    # string in the list
    if test in suite[system]:
        print(test)
        return False;
    else:
        return True