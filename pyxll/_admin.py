import ctypes
import contextlib
from ctypes import wintypes

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)

ERROR_ACCESS_DENIED = 5
ERROR_INSUFFICIENT_BUFFER = 122
ERROR_NO_TOKEN = 1008
ERROR_NOT_ALL_ASSIGNED = 1300

# TOKEN_TYPE
TokenPrimary = 1
TokenImpersonation = 2

# SECURITY_IMPERSONATION_LEVEL
SecurityAnonymous = 0
SecurityIdentification = 1
SecurityImpersonation = 2
SecurityDelegation = 3

# TOKEN_INFORMATION_CLASS
TokenUser = 1
TokenGroups = 2
TokenPrivileges = 3
TokenOwner = 4

# WELL_KNOWN_SID_TYPE
WinBuiltinAdministratorsSid = 26

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

TOKEN_ASSIGN_PRIMARY    = 0x0001
TOKEN_DUPLICATE         = 0x0002
TOKEN_IMPERSONATE       = 0x0004
TOKEN_QUERY             = 0x0008
TOKEN_QUERY_SOURCE      = 0x0010
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_ADJUST_GROUPS     = 0x0040
TOKEN_ADJUST_DEFAULT    = 0x0080
TOKEN_ADJUST_SESSIONID  = 0x0100
TOKEN_ALL_ACCESS = 0x000F0000 | 0x01FF

SE_PRIVILEGE_ENABLED_BY_DEFAULT = 0x00000001
SE_PRIVILEGE_ENABLED            = 0x00000002
SE_PRIVILEGE_REMOVED            = 0x00000004
SE_PRIVILEGE_USED_FOR_ACCESS    = 0x80000000

SE_GROUP_MANDATORY          = 0x00000001
SE_GROUP_ENABLED_BY_DEFAULT = 0x00000002
SE_GROUP_ENABLED            = 0x00000004
SE_GROUP_OWNER              = 0x00000008
SE_GROUP_USE_FOR_DENY_ONLY  = 0x00000010
SE_GROUP_INTEGRITY          = 0x00000020
SE_GROUP_INTEGRITY_ENABLED  = 0x00000040
SE_GROUP_LOGON_ID           = 0xC0000000
SE_GROUP_RESOURCE           = 0x20000000

SE_CREATE_TOKEN_NAME           = 'SeCreateTokenPrivilege'
SE_ASSIGNPRIMARYTOKEN_NAME     = 'SeAssignPrimaryTokenPrivilege'
SE_LOCK_MEMORY_NAME            = 'SeLockMemoryPrivilege'
SE_INCREASE_QUOTA_NAME         = 'SeIncreaseQuotaPrivilege'
SE_MACHINE_ACCOUNT_NAME        = 'SeMachineAccountPrivilege'
SE_TCB_NAME                    = 'SeTcbPrivilege'
SE_SECURITY_NAME               = 'SeSecurityPrivilege'
SE_TAKE_OWNERSHIP_NAME         = 'SeTakeOwnershipPrivilege'
SE_LOAD_DRIVER_NAME            = 'SeLoadDriverPrivilege'
SE_SYSTEM_PROFILE_NAME         = 'SeSystemProfilePrivilege'
SE_SYSTEMTIME_NAME             = 'SeSystemtimePrivilege'
SE_PROF_SINGLE_PROCESS_NAME    = 'SeProfileSingleProcessPrivilege'
SE_INC_BASE_PRIORITY_NAME      = 'SeIncreaseBasePriorityPrivilege'
SE_CREATE_PAGEFILE_NAME        = 'SeCreatePagefilePrivilege'
SE_CREATE_PERMANENT_NAME       = 'SeCreatePermanentPrivilege'
SE_BACKUP_NAME                 = 'SeBackupPrivilege'
SE_RESTORE_NAME                = 'SeRestorePrivilege'
SE_SHUTDOWN_NAME               = 'SeShutdownPrivilege'
SE_DEBUG_NAME                  = 'SeDebugPrivilege'
SE_AUDIT_NAME                  = 'SeAuditPrivilege'
SE_SYSTEM_ENVIRONMENT_NAME     = 'SeSystemEnvironmentPrivilege'
SE_CHANGE_NOTIFY_NAME          = 'SeChangeNotifyPrivilege'
SE_REMOTE_SHUTDOWN_NAME        = 'SeRemoteShutdownPrivilege'
SE_UNDOCK_NAME                 = 'SeUndockPrivilege'
SE_SYNC_AGENT_NAME             = 'SeSyncAgentPrivilege'
SE_ENABLE_DELEGATION_NAME      = 'SeEnableDelegationPrivilege'
SE_MANAGE_VOLUME_NAME          = 'SeManageVolumePrivilege'
SE_IMPERSONATE_NAME            = 'SeImpersonatePrivilege'
SE_CREATE_GLOBAL_NAME          = 'SeCreateGlobalPrivilege'
SE_TRUSTED_CREDMAN_ACCESS_NAME = 'SeTrustedCredManAccessPrivilege'
SE_RELABEL_NAME                = 'SeRelabelPrivilege'
SE_INC_WORKING_SET_NAME        = 'SeIncreaseWorkingSetPrivilege'
SE_TIME_ZONE_NAME              = 'SeTimeZonePrivilege'
SE_CREATE_SYMBOLIC_LINK_NAME   = 'SeCreateSymbolicLinkPrivilege'

class HANDLE(wintypes.HANDLE):
    __slots__ = ('closed',)

    def detach(self):
        if not getattr(self, 'closed', False):
            self.closed = True
            value = int(self)
            self.value = None
            return value
        raise ValueError("already closed")

    def close(self, *, CloseHandle=kernel32.CloseHandle):
        if self and not getattr(self, 'closed', False):
            CloseHandle(self.detach())

    def __enter__(self):
        return self

    def __exit__(self, cls, value, traceback):
        self.close()

    def __int__(self):
        return self.value or 0

    def __repr__(self):
        return "%s(%d)" % (self.__class__.__name__, int(self))

    __del__ = close

PHANDLE = ctypes.POINTER(HANDLE)

class LUID(ctypes.Structure):
    _fields_ = (('LowPart',  wintypes.DWORD),
                ('HighPart', wintypes.LONG))
    @property
    def value(self):
        return ctypes.c_longlong.from_buffer(self).value

    @value.setter
    def value(self, v):
        ctypes.c_longlong.from_buffer(self).value = v

PLUID = ctypes.POINTER(LUID)

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = (('Luid',       LUID),
                ('Attributes', wintypes.DWORD))

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = (('PrivilegeCount', wintypes.DWORD),
                ('_Privileges', LUID_AND_ATTRIBUTES * 0))

    def __init__(self, PrivilegeCount=1, *args):
        super(TOKEN_PRIVILEGES, self).__init__(PrivilegeCount, *args)
        if PrivilegeCount < 0:
            raise ValueError('PrivilegeCount must be non-negative.')
        if PrivilegeCount > 0:
            ctypes.resize(self, ctypes.sizeof(self) +
                          PrivilegeCount * ctypes.sizeof(LUID_AND_ATTRIBUTES))

    @property
    def Privileges(self):
        dtype = LUID_AND_ATTRIBUTES * self.PrivilegeCount
        offset = type(self)._Privileges.offset
        return dtype.from_buffer(self, offset)

PTOKEN_PRIVILEGES = ctypes.POINTER(TOKEN_PRIVILEGES)

class SID_IDENTIFIER_AUTHORITY(ctypes.Structure):
    _fields_ = (('Value', ctypes.c_ubyte * 6),)

class SID(ctypes.Structure):
    _fields_ = (('Revision', ctypes.c_ubyte),
                ('SubAuthorityCount', ctypes.c_ubyte),
                ('IdentifierAuthority', SID_IDENTIFIER_AUTHORITY),
                ('_SubAuthority', wintypes.DWORD * 0))

    def __init__(self, Revision=1, SubAuthorityCount=1, *args):
        super(SID, self).__init__(Revision, SubAuthorityCount, *args)
        if SubAuthorityCount < 0:
            raise ValueError('SubAuthorityCount must be non-negative.')
        if SubAuthorityCount > 0:
            ctypes.resize(self, ctypes.sizeof(self) + 4 * SubAuthorityCount)

    @property
    def SubAuthority(self):
        dtype = wintypes.DWORD * self.SubAuthorityCount
        offset = type(self)._SubAuthority.offset
        address = ctypes.addressof(self) + offset
        array = dtype.from_address(address)
        array._obj = self
        return array

    def __bytes__(self):
        size = ctypes.sizeof(SID) + 4 * self.SubAuthorityCount
        array = (ctypes.c_char * size).from_address(ctypes.addressof(self))
        return array[:]

PSID = ctypes.POINTER(SID)

class SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = (('Sid', PSID),
                ('Attributes', wintypes.DWORD))

class TOKEN_GROUPS(ctypes.Structure):
    _fields_ = (('GroupCount', wintypes.DWORD),
                ('_Groups', SID_AND_ATTRIBUTES * 0))

    def __init__(self, GroupCount=1, *args):
        super(TOKEN_GROUPS, self).__init__(GroupCount, *args)
        if GroupCount < 0:
            raise ValueError('GroupCount must be non-negative.')
        if GroupCount > 0:
            ctypes.resize(self, ctypes.sizeof(self) +
                          GroupCount * ctypes.sizeof(SID_AND_ATTRIBUTES))

    @property
    def Groups(self):
        dtype = SID_AND_ATTRIBUTES * self.GroupCount
        offset = type(self)._Groups.offset
        return dtype.from_buffer(self, offset)

PTOKEN_GROUPS = ctypes.POINTER(TOKEN_GROUPS)

def _nonzero_success(result, func, args):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return args

advapi32.LookupPrivilegeValueW.errcheck = _nonzero_success
advapi32.LookupPrivilegeValueW.argtypes = (
    wintypes.LPCWSTR, # _In_opt_ lpSystemName
    wintypes.LPCWSTR, # _In_     lpName
    PLUID)            # _Out_    lpLuid

advapi32.CreateWellKnownSid.errcheck = _nonzero_success
advapi32.CreateWellKnownSid.argtypes = (
    wintypes.DWORD,  # WellKnownSidType,
    ctypes.c_char_p, # DomainSid
    ctypes.c_char_p, # pSid
    wintypes.PDWORD) # cbSid

kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
kernel32.GetCurrentProcess.restype = wintypes.HANDLE
kernel32.GetCurrentThread.restype = wintypes.HANDLE

kernel32.OpenProcess.errcheck = _nonzero_success
kernel32.OpenProcess.restype = HANDLE
kernel32.OpenProcess.argtypes = (
    wintypes.DWORD, # _In_ dwDesiredAccess
    wintypes.BOOL,  # _In_ bInheritHandle
    wintypes.DWORD) # _In_ dwProcessId

advapi32.OpenProcessToken.errcheck = _nonzero_success
advapi32.OpenProcessToken.argtypes = (
    wintypes.HANDLE,  # _In_  ProcessHandle
    wintypes.DWORD,   # _In_  DesiredAccess
    PHANDLE)          # _Out_ TokenHandle

advapi32.OpenThreadToken.errcheck = _nonzero_success
advapi32.OpenThreadToken.argtypes = (
    wintypes.HANDLE,  # _In_ ThreadHandle
    wintypes.DWORD,   # _In_ DesiredAccess
    wintypes.BOOL,    # _In_ OpenAsSelf
    PHANDLE)          # _Out_ TokenHandle

advapi32.SetThreadToken.errcheck = _nonzero_success
advapi32.SetThreadToken.argtypes = (
    wintypes.PHANDLE, # Thread
    wintypes.HANDLE)  # Token

advapi32.DuplicateTokenEx.argtypes = (
    wintypes.HANDLE, # hExistingToken
    wintypes.DWORD,  # dwDesiredAccess
    wintypes.LPVOID, # lpTokenAttributes
    wintypes.DWORD,  # ImpersonationLevel
    wintypes.DWORD,  # TokenType
    PHANDLE)         # phNewToken

advapi32.GetTokenInformation.errcheck = _nonzero_success
advapi32.GetTokenInformation.argtypes = (
    wintypes.HANDLE, # _In_      TokenHandle
    wintypes.DWORD,  # _In_      TokenInformationClass
    wintypes.LPVOID, # _Out_opt_ TokenInformation
    wintypes.DWORD,  # _In_      TokenInformationLength
    wintypes.PDWORD) # _Out_     ReturnLength

advapi32.CheckTokenMembership.errcheck = _nonzero_success
advapi32.CheckTokenMembership.argtypes = (
    wintypes.HANDLE, # TokenHandle
    ctypes.c_char_p, # SidToCheck
    wintypes.PBOOL)  # IsMember

advapi32.AdjustTokenPrivileges.errcheck = _nonzero_success
advapi32.AdjustTokenPrivileges.argtypes = (
    wintypes.HANDLE,   # _In_      TokenHandle
    wintypes.BOOL,     # _In_      DisableAllPrivileges
    PTOKEN_PRIVILEGES, # _In_opt_  NewState
    wintypes.DWORD,    # _In_      BufferLength
    PTOKEN_PRIVILEGES, # _Out_opt_ PreviousState
    wintypes.PDWORD)   # _Out_opt_ ReturnLength

def create_well_known_sid(sid_type):
    sid = (ctypes.c_char * 1)()
    cbSid = wintypes.DWORD()
    try:
        advapi32.CreateWellKnownSid(sid_type, None, sid, ctypes.byref(cbSid))
    except OSError as e:
        if e.winerror != ERROR_INSUFFICIENT_BUFFER:
            raise
        sid = (ctypes.c_char * cbSid.value)()
        advapi32.CreateWellKnownSid(sid_type, None, sid, ctypes.byref(cbSid))
    return sid[:]

def adjust_token_privileges(hToken, new_state=(), disable_all=False,
                            return_previous_state=True):
    pNewState = PTOKEN_PRIVILEGES()
    pPreviousState = PTOKEN_PRIVILEGES()
    pReturnLength = wintypes.PDWORD()
    bufferLength = 0
    if not disable_all:
        newState = TOKEN_PRIVILEGES(len(new_state))
        pNewState.contents = newState
        for priv, (luid, attr) in zip(newState.Privileges, new_state):
            priv.Luid.value = luid
            priv.Attributes = attr
    if return_previous_state:
        previousState = TOKEN_PRIVILEGES(len(new_state))
        returnLength = wintypes.DWORD()
        bufferLength = ctypes.sizeof(previousState)
        pPreviousState.contents = previousState
        pReturnLength.contents = returnLength
    while True:
        try:
            advapi32.AdjustTokenPrivileges(hToken, disable_all,
                                           pNewState, bufferLength, pPreviousState, pReturnLength)
            break
        except OSError as e:
            if (not return_previous_state
                    or e.winerror != ERROR_INSUFFICIENT_BUFFER):
                raise
            bufferLength = returnLength.value
            ctypes.resize(previousState, bufferLength)
            pPreviousState.contents = previousState
    if not return_previous_state:
        return []
    return [(p.Luid.value, p.Attributes) for p in previousState.Privileges]

def enable_token_privileges(hToken, *privilege_names):
    luid = LUID()
    state = []
    for name in privilege_names:
        advapi32.LookupPrivilegeValueW(None, name, ctypes.byref(luid))
        state.append((luid.value, SE_PRIVILEGE_ENABLED))
    return adjust_token_privileges(hToken, state)

@contextlib.contextmanager
def open_effective_token(access, open_as_self=True):
    """Open the effective token of the current thread.

    If the current thread is not already impersonating, it first
    impersonates the token of the current process, which allows enabling
    privileges and groups only for the current thread.
    """
    hThread = kernel32.GetCurrentThread()
    hToken = HANDLE()
    access |= TOKEN_IMPERSONATE
    try:
        advapi32.OpenThreadToken(hThread, access, open_as_self,
                                 ctypes.byref(hToken))
        impersonated_self = False
    except OSError as e:
        if e.winerror != ERROR_NO_TOKEN:
            raise
        hProcess = kernel32.GetCurrentProcess()
        hTokenProcess = HANDLE()
        advapi32.OpenProcessToken(hProcess, TOKEN_DUPLICATE,
                                  ctypes.byref(hTokenProcess))
        with hTokenProcess:
            advapi32.DuplicateTokenEx(hTokenProcess, access, None,
                                      SecurityImpersonation, TokenImpersonation,
                                      ctypes.byref(hToken))
        advapi32.SetThreadToken(None, hToken)
        impersonated_self = True
    try:
        yield hToken
    finally:
        with hToken:
            if impersonated_self:
                advapi32.SetThreadToken(None, None)

@contextlib.contextmanager
def enable_privileges(*privilege_names):
    """Enable a set of privileges for the current thread."""
    access = TOKEN_QUERY | TOKEN_ADJUST_PRIVILEGES
    with open_effective_token(access) as hToken:
        prev_state = enable_token_privileges(hToken, *privilege_names)
        try:
            yield
        finally:
            if prev_state:
                adjust_token_privileges(hToken, prev_state)

def get_primary_token(pid, access=TOKEN_QUERY):
    hToken = HANDLE()
    with enable_privileges(SE_DEBUG_NAME):
        hProcess = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    with hProcess:
        advapi32.OpenProcessToken(hProcess, access, ctypes.byref(hToken))
    return hToken

def get_identification_token(pid, access=TOKEN_QUERY):
    hToken = HANDLE()
    with enable_privileges(SE_DEBUG_NAME):
        hProcess = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    with hProcess:
        hTokenProcess = HANDLE()
        advapi32.OpenProcessToken(hProcess, TOKEN_DUPLICATE,
                                  ctypes.byref(hTokenProcess))
        with hTokenProcess:
            advapi32.DuplicateTokenEx(hTokenProcess, access, None,
                                      SecurityIdentification, TokenImpersonation,
                                      ctypes.byref(hToken))
    return hToken

def check_token_membership(hToken, pSid):
    isAdmin = wintypes.BOOL()
    advapi32.CheckTokenMembership(hToken, pSid, ctypes.byref(isAdmin))
    return bool(isAdmin)

def get_token_groups(hToken):
    tokenGroups = TOKEN_GROUPS()
    returnLength = wintypes.DWORD()
    while True:
        try:
            advapi32.GetTokenInformation(hToken, TokenGroups,
                                         ctypes.byref(tokenGroups), ctypes.sizeof(tokenGroups),
                                         ctypes.byref(returnLength))
            break
        except OSError as e:
            if e.winerror != ERROR_INSUFFICIENT_BUFFER:
                raise
            ctypes.resize(tokenGroups, returnLength.value)
    return [(bytes(g.Sid[0]), g.Attributes) for g in tokenGroups.Groups]

def process_user_is_admin(pid):
    adminSid = create_well_known_sid(WinBuiltinAdministratorsSid)
    try:
        with get_identification_token(pid) as hToken:
            return check_token_membership(hToken, adminSid)
    except OSError as e:
        if e.winerror != ERROR_ACCESS_DENIED:
            raise
    with get_primary_token(pid) as hToken:
        groups = get_token_groups(hToken)
    for sid, attributes in groups:
        if sid == adminSid:
            return bool(attributes & SE_GROUP_ENABLED)
    return False