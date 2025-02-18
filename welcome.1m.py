#!/usr/bin/env -S uv run -s

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "aiohttp",
#     "pycountry",
#     "pydantic",
#     "pydantic-extra-types",
#     "yarl",
# ]
# ///

# <xbar.title>Welcome</xbar.title>
# <swiftbar.hideAbout>true</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideLastUpdated>true</swiftbar.hideLastUpdated>
# <swiftbar.hideDisablePlugin>true</swiftbar.hideDisablePlugin>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>

from contextlib import contextmanager
from enum import Enum
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any, cast
import aiohttp
import asyncio
import base64
import os
from collections import OrderedDict, defaultdict
from yarl import URL
from aiohttp.cookiejar import CookieJar
import pickle
from pydantic import BaseModel, ConfigDict
from pydantic_extra_types.country import CountryAlpha2
import urllib.parse


MENUBAR_ICON_B64 = "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"

b64_prefix = "iVBORw0KGgoAAAANSUhEUgAAACIAAAAiCAQAAACQTsNJAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAmJLR0QAAKqNIzIAAAAJcEhZcwAAFiUAABYlAUlSJPAAAAAHdElNRQfmDB4A"
MENUBAR_NUMBER_ICONS_B64 = {
    -1: MENUBAR_ICON_B64,
    0: "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",
    1: f"{b64_prefix}Mh5ugPaAAAAAAW9yTlQBz6J3mgAAAqZJREFUSMfdk01r1FAUhp+b3CSdzIx1oFCtBb9AF0JRClppF4IoflMRnboRwYVLFVeCf8KFUEF04Y9wp/4ClX5YwSq4VBARp9NOppnXRTJfnelMBVeekHBv7nue3POeG2gN0zbyYdsZ+9v5FZxOZlsJA2eDwX3s3bMjSTow7QohVLgAeFtCDOXtkhFlK3sf9hdDIRMRIVc7L28FY+B4JvMZUXU0UjxyMhAyFYSoIE+jV7aC8SB8gogpDT/ICJk1NDDvzycjI7fYH2OB54gqMSnCfDmYH8qbL4g1hOiLscAzRBVRo4LM8mABYM/2zCfEKqLvbizwNIVUUGFpfBCwWJjM5xbrGGZ6YQLgBWKdCGWWpwoNsYWxbLDQwBQ3Ozc+uNfrvch/mMwDFhcHB3cjJnet2258cGdQYmC4eCIH2LYTbGE89OcTjKddHRgP/CJKBNkE0TWaGKuR6daiPHAbiIHFsWyvFo6Hdh6ZVeSqcLGO8SDTQIQLY9m0T/V4jRALzQ6Oh95cojYKz6dFDV2yqZ1BJ+JO8gM2IGBhNGPnkgwj9xwQnDFCRCh4dyjXhrA8pNYBAQsjoX2bZKHsKbwfyETEKHOsxagst1lMARsh4IN3FBGbCIXfrRtVkUcNVg0Qp7KrzHb11aBEVXUAyQOtO4Vr3hv7EadNWp+t8KgD0hqu+ey9ys0k41sIMQG46X2TFWYZ5XBHOXXFBELOvcSkgEocdGz7JcOUgCF6Rs0HAksMqH0F+LZ5XttMQOx0kWlD5Z3GbnjndJVqU0jXFYd/EP8ZxPZZf9+jU10hDuCmSes99S5xaw2tkBIQ9fnoeuNZAtKWNyHiMV/x206CKBMCK2TbyjJE7EYY3CZEgJhi6q/8rGGaaAvcQPykRI1y36tGmVVKiLtJ9h9VdSnLjFBUtQAAAIRlWElmTU0AKgAAAAgABQESAAMAAAABAAEAAAEaAAUAAAABAAAASgEbAAUAAAABAAAAUgEoAAMAAAABAAIAAIdpAAQAAAABAAAAWgAAAAAAAACQAAAAAQAAAJAAAAABAAOgAQADAAAAAQABAACgAgAEAAAAAQAAACKgAwAEAAAAAQAAACIAAAAAEEJAwQAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAyMi0xMi0zMFQwMDo1MDoyOSswMDowMMZvJ60AAAAldEVYdGRhdGU6bW9kaWZ5ADIwMjItMTItMzBUMDA6NTA6MjkrMDA6MDC3Mp8RAAAAEXRFWHRleGlmOkNvbG9yU3BhY2UAMQ+bAkkAAAASdEVYdGV4aWY6RXhpZk9mZnNldAA5MFmM3psAAAAXdEVYdGV4aWY6UGl4ZWxYRGltZW5zaW9uADM0Yc/CIgAAABd0RVh0ZXhpZjpQaXhlbFlEaW1lbnNpb24AMzS8WRunAAAAAElFTkSuQmCC",
    2: f"{b64_prefix}Mg3qPrdeAAAAAW9yTlQBz6J3mgAAAxJJREFUSMedlNuLFEcUh7/qrp52emayGVhRVyVeMAZCFnTBC67xGlETxSBk9EUIIeQ1QV98l5B/IATFy4Pgn+CT5kJInryA62YC2SiCbIhgVJzspWd7fnnomp6Z3dmd3ZyCpqpOna/q/M6hod1MxywHbxy2r71X4aF0tRgzcCTs28D6dSvToLdP+EIIlT8CgkUh+ku2asSElT0LGyuRkImJka9VHy8GY2BnPv8nou5poLLlQChkphFiGgVac3IxmACii4iE2orzeSEzhZaN5EbSmZFf6Y2xwDVEnQSHMI82l/pL5hFiCiF6YixwFVFHNJhGZqyvDLDuzfwfiElEz9dY4LKDTKNydagPsFjYVSqONjGcWggTAtcRM8QoPzZczg5bGCyEDzNMZb6+yYF/ulmL0m+7SoDFx8PDn40pftLtNTnwT6FUwGh0bxGwHR1sYSjKjaSYQKvnYALIVVB6oJAiuloLYzVwoj2pAPwMsWx0sLBQCYciO4LMJPJVPtbEBJDPENHDwYKrU8g5fuUZdV5S5Ts2NSUeioIH6Wmj6EOXVP9x6+QMW4gSd1DHmOJAE7Mmbx+kEUb+USA8bISIUXj/3aJDwDdZ8BNXVvHUKWBhILL30ihU+IDgOTIxCcpvbxPqLxf4OTDAU7fa06plsA2RmBhFzzw/BgUAkwZIACjzmDFe8Q+XgXF+dMFlV/QE6h4gBaAZVu0OfrBVhNgB+AB4LihdlRh3L3nHeXxgB0JmLLi9/P1077MOiN9R0yK3HOKnDJBBvK/SO0NIwnnbYgO/uKq85Iu57kYOCD0SQJ2ebHaIOwwC8DcH+X2WFxeZeHPpyMn3KTcpA/AzW7kLgJl1IYDpBkn5Z7ji1PmafYy3eeaYnUeL97jk3vM9VU673fuMLgVygabY+9mf7Z7vDumezlqOswTrDtm9FMR86dzgxv+FeIDv5JxZ8LxP0p5DO6QGxD0uncm+NcCVvAUR3/KEXEcniAki4F8KbT9tMMS8hTBpJ9mMJ4YZXpKeDUwLbYEziBfUaDDRczSYYJIa4ss0+j/opE38m5vTIQAAAIRlWElmTU0AKgAAAAgABQESAAMAAAABAAEAAAEaAAUAAAABAAAASgEbAAUAAAABAAAAUgEoAAMAAAABAAIAAIdpAAQAAAABAAAAWgAAAAAAAACQAAAAAQAAAJAAAAABAAOgAQADAAAAAQABAACgAgAEAAAAAQAAACKgAwAEAAAAAQAAACIAAAAAEEJAwQAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAyMi0xMi0zMFQwMDo1MDoxMiswMDowMErndLQAAAAldEVYdGRhdGU6bW9kaWZ5ADIwMjItMTItMzBUMDA6NTA6MTIrMDA6MDA7uswIAAAAEXRFWHRleGlmOkNvbG9yU3BhY2UAMQ+bAkkAAAASdEVYdGV4aWY6RXhpZk9mZnNldAA5MFmM3psAAAAXdEVYdGV4aWY6UGl4ZWxYRGltZW5zaW9uADM0Yc/CIgAAABd0RVh0ZXhpZjpQaXhlbFlEaW1lbnNpb24AMzS8WRunAAAAAElFTkSuQmCC",
    3: f"{b64_prefix}MTcHHz0vAAAAAW9yTlQBz6J3mgAAAzlJREFUSMeNk8uLHFUUh79bdasrVT3t2GGCZjJifI0LYYKMaGJGDRpjfBIR0nHjxp0uNOhGwbVuBBUSiIgudJG/QYkPVFypIZ3JLBwjgYFAgiaanu6Z6sfPRd2urp7pnu5TUNx77jnfPa8LeTF9qwLcdNje8P4ND6W7ccTA0+Hkndyx+9bUafaIL4RQ+TkgGAsxVbJLRtSt7FtwVyUWMgkJ8rXzxXEwBvZF0Z+Ipqfpyv1PhEJmHSHWUaCZl8bBBBCfQrSp3fJOJGTW0LZqoZqujPzKaIwFvkA0aeMQ5uK9pamSuYhYQ4iRGAt8jmgiOqwjszxZBth9c/QHooEYGY0FPnOQdVRemp8ELBb2lyYWuxiObYUJgS8RLRIULS+UM2MLc8XwfIapDJubAvgvd3tRurC/BFh8PDz8jZiJo4OiKYB/DKUFjBcPTAC2b4ItzMeFaooJtGsTJoBCBaUGxRQxUHoYq+kj+aQC8DPEtsW54lYtnI9tFZkG8lV+vosJIMoQ8fm5outTxNv8wnVa/MdZPmBHt8TzcXAutTaKn3VJTb1gXTnDHqLIT6jvW2Gmi5mJ7LnUw8h/BggPGyESFP5+34RDwMfO9SyfsuLWp3rzNB3b31IvVHyS4G9kEtooeigrlOFrVhGXiYB9DvJjvpfBg4i2SVB8xfpJEwV0oGGANgDiEB6zbKcBzDrXC4BBqVXTA6QA1GLnI8F3dgkh9gI+AF5251G+SZ8jl9iVnfjAXoTMcnBmx6Op7tU+iJ/r6IculTUqTuPnId7x9M4Q2uHQsdievavTnNh83CkAoUcbUP9Jbv0eMQe5AcBrPLzhNPVse5vpKPdmVmhwhq/c7oArbL8YOzCJEo9zD3dT5zgA/zh9awAiG62N4nOaEEj4hL/weMrpfx1cOG+g9pqbzgI/8BE/8wAAVb4dDBkcCbzLHh4DbuMNp7lMZXAywyKBVQ7yOt9zlSbXqfI+e1gaYjs0EmhxkpOMJXmIB/iuva0t7X3a+RzykBqQjLi0lf1rgBvTHkSc4BKFvuKJOjGwSjE3gGBIuB1h0ndmM55YYGG8GjjpYHpoC7yCuEaNDvWRX4c6DWqIN1Pv/wF0NFq4HfyIWAAAAIRlWElmTU0AKgAAAAgABQESAAMAAAABAAEAAAEaAAUAAAABAAAASgEbAAUAAAABAAAAUgEoAAMAAAABAAIAAIdpAAQAAAABAAAAWgAAAAAAAACQAAAAAQAAAJAAAAABAAOgAQADAAAAAQABAACgAgAEAAAAAQAAACKgAwAEAAAAAQAAACIAAAAAEEJAwQAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAyMi0xMi0zMFQwMDo0OTo1NCswMDowMJDmu34AAAAldEVYdGRhdGU6bW9kaWZ5ADIwMjItMTItMzBUMDA6NDk6NTQrMDA6MDDhuwPCAAAAEXRFWHRleGlmOkNvbG9yU3BhY2UAMQ+bAkkAAAASdEVYdGV4aWY6RXhpZk9mZnNldAA5MFmM3psAAAAXdEVYdGV4aWY6UGl4ZWxYRGltZW5zaW9uADM0Yc/CIgAAABd0RVh0ZXhpZjpQaXhlbFlEaW1lbnNpb24AMzS8WRunAAAAAElFTkSuQmCC",
    4: f"{b64_prefix}MSSDoXzxAAAAAW9yTlQBz6J3mgAAAuRJREFUSMetk8+LFEcUxz/VXd3t9My4GVhJshHcKEQhsCALurJLCAQTf7NBdNZLLoJnJaeQox78AxQURA9evIRAbjkk+BcYcF03IetPPAkqksmu2zs93xyqZ6Z7Z9yZhbymu+tVvfep9+q9gryYwiiErYfsP97b6GunDSMGDkcjO/l0/CPn9NmsL4RQ7RgQDIUYrdpFI5at7Pewqx4LmYQE+fr422EwBg6USo8Qa57G6nu/ioTMKkKsokDbTw6DCSC+jkhpfPhDSci8Q1vmw3k3MvLrgzEWuIVYIyVDmMe7q6NV8xjxDiEGYixwE7GGaLGKzNJIDWD8g9LfiBXEwGgscCODrKLa4uQIYLEwXa0stDHMbYSJgNuIJgkqLc3UOsYWJsrRgw6m/r6+CcE/065F9eF0FbD4eHj46zGV0/2iCcGfQ+4A44UvK4AtdLCFyTicd5hAn/RgAgjryBmUHaKvdDFWY7P5pALwO4gtCxPljUo4Gdt5ZFaQr9rxNiaAUgcRP5goZ3Xq1uw3d38YdyuTcXDfWRvFR7OkRk/Y7DijXgRcyRAOAha2l+x952HkHwGiQ0aIBEV/fF7pQZzrINoQsDAW23vOC5UPErxCJiFFpf091f/Cma2DQAjBPkRqEhS/9PwEFACsGCDNIcb5iQD4Kzfnip7CmgdIAajp1U4Hd+2feIUIPKDCL4wCv3KxB9IW3zwKfq/MufFZhJgC/Ow1/IwQi4wwV0inbTGFkHfB7RlBGvW0w0Vmgdcc5+1GXdMKgcgjBVRc4SQ/Ak1OsdTrV9AEpLYPXhzstFlenvCKbes2BDAemxP1m9wspK/YvrOXuJbTvuEyAEd5vhnIC17ktD3Z/yFP+0P+l3SGgdzBYDDvi6OYjgf4WWM3N7T3SfPb5yENIBkQVbPzbQBZybsQcZVnhIVOEMvEwL+UC1fPkLADYfC7EAFihplNnWcL00Vb4DvEGxq0WB74tFhmhQbivPP+D4iLNOI/Btu1AAAAhGVYSWZNTQAqAAAACAAFARIAAwAAAAEAAQAAARoABQAAAAEAAABKARsABQAAAAEAAABSASgAAwAAAAEAAgAAh2kABAAAAAEAAABaAAAAAAAAAJAAAAABAAAAkAAAAAEAA6ABAAMAAAABAAEAAKACAAQAAAABAAAAIqADAAQAAAABAAAAIgAAAAAQQkDBAAAAJXRFWHRkYXRlOmNyZWF0ZQAyMDIyLTEyLTMwVDAwOjQ5OjM1KzAwOjAw8P65TQAAACV0RVh0ZGF0ZTptb2RpZnkAMjAyMi0xMi0zMFQwMDo0OTozNSswMDowMIGjAfEAAAARdEVYdGV4aWY6Q29sb3JTcGFjZQAxD5sCSQAAABJ0RVh0ZXhpZjpFeGlmT2Zmc2V0ADkwWYzemwAAABd0RVh0ZXhpZjpQaXhlbFhEaW1lbnNpb24AMzRhz8IiAAAAF3RFWHRleGlmOlBpeGVsWURpbWVuc2lvbgAzNLxZG6cAAAAASUVORK5CYII=",
    5: f"{b64_prefix}MRCiFYhEAAAAAW9yTlQBz6J3mgAAAy5JREFUSMeVk91rHFUYxn9nzpmZzuxu40pAm0YatWhBCEhsiDQXgijxu0XoxguLoPcqeqP/Q0EvWqiIXoi33mi9EaI3pRashW5iKrZFLV5oaYt23W12d/bxYmY/JtlN1meYnTN7nvc357zve2BQJjcKYPeSu+39HT6dvo0jA8+EEw9w/8y9adBDh60QQuXnAX8sxGTJrRtRd3LvwIOVWMg0aSKrPUfGwRh4PIquIFqepiqPPhkKmQ2E2EC+pl8eB+NDfAqRULvnvUjI3EG7qkE1HRnZys4YB3yKaJGQIczVh0uTJXMVcQchdsQ44BNEC9FhA5nLE2WAmbuiXxANxI6rccDHGWQDldfnJgCHg0Ol4loXw/J2mBD4DNGmiaLLi+We2cFsIVztYSqj+iYA+0q3FqWfDpUAh8XDw27GFI8OW00AdhmlCYzXnigCLtfBDubioJpifO3dgvEhqKDUUEgRQ9XHOE0dHtyUD7aH2LU2W9iuhHOxqyLTQFblF7oYH6IeIl6dLWR1+hxtun5NZ+Zi/2LqNoqfyzY1+aLL0hn2EXB+KAQcTEfuYhphZJ8FwiUjRBOFFx4p9hBwewQEHEzF7sc0ChWeMv6N1t2mJYsXLTTOEdAE4D5+B+Ajvuylo85Kr5ZNf751jo5J5MfXnW22kE8HGgZIMtuB7Hmar3J5NSh1tTxA8kFtr3zU/85dwstZvR7kJarUuclpFjPIoKy54q8Ul9Px6wixANjsPrElI21eTc3ZvYCQ93b6zRCScEs7dFdS5SQXsuBT7Nls6wRA6EgA5WeA1zjAfiI+JMFyloNAxBFO0sl5BSSOrRKGa1zjm+w94WsOArAvS2xeZhgELHuZZpoWX+TSeX0IYqC18trPOgD/cIY/8VjK/v92qHtTabu6lLXYbr7nA84wD8AK5/8PBN5gFYAZ3mQBgJ85NsI7EvIX87zLWW6RcJMfeJ/H+GMUxI2aoMFxjjOWBiEeYLNKtLf1W5LBPQxCapCd4dFq935rQNamfYg4wW8EuU4QdWLgXwq5o2dosg9hsH2IALGYndRx1cH00Q44hrhFjQ71Ha8OdRrUEG+l0f8BZTxhY7LL2zAAAACEZVhJZk1NACoAAAAIAAUBEgADAAAAAQABAAABGgAFAAAAAQAAAEoBGwAFAAAAAQAAAFIBKAADAAAAAQACAACHaQAEAAAAAQAAAFoAAAAAAAAAkAAAAAEAAACQAAAAAQADoAEAAwAAAAEAAQAAoAIABAAAAAEAAAAioAMABAAAAAEAAAAiAAAAABBCQMEAAAAldEVYdGRhdGU6Y3JlYXRlADIwMjItMTItMzBUMDA6NDk6MTUrMDA6MDCy274wAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDIyLTEyLTMwVDAwOjQ5OjE1KzAwOjAww4YGjAAAABF0RVh0ZXhpZjpDb2xvclNwYWNlADEPmwJJAAAAEnRFWHRleGlmOkV4aWZPZmZzZXQAOTBZjN6bAAAAF3RFWHRleGlmOlBpeGVsWERpbWVuc2lvbgAzNGHPwiIAAAAXdEVYdGV4aWY6UGl4ZWxZRGltZW5zaW9uADM0vFkbpwAAAABJRU5ErkJggg==",
    6: f"{b64_prefix}MDiOuxH/AAAAAW9yTlQBz6J3mgAAAzhJREFUSMeNk8tvG1UUxn935o4nM7YJFpFKQqWWh4popUhgCVo1CxAPlUeggBQnC7rpquqmCAmJBRtWiB0LFgUEQqxQi1QJVoiX+AMoahJa1LTAAooCFVAcO3Yy/ljM9WTs2onPSPa58jk/n/udbyAfpicrwC1H7H/ev+ET6WmUMPBkOH4Xd+69PW3ad9QXQqjyDBCMhJgo24tGNKzsK3B3LRYybdrI1+Tzo2AMHIqiK4gNT1O1+x8NhUwLIVoo0O4XR8EEEJ9GJNR3vRYJmXU0tlhYTDMjv7YzxgIfIjZIcAhz9d7yRNlcRawjxI4YC3yA2EB0aCGzMl4B2HtrdBnRROw4jQXed5AWqlysjgMWC4fLpeUuhvntMCHwMWKTNopWZipZsYXpYriUYWrDfFMAf6G7i/KPh8uAxcfDw+/HlOYGTVMAfx6lAsbLD5cA2+NgC9W4sJhiAt1xEyaAQg2lBcUUMTC2MFZTR/OXCsDPEGPL08XtVliN7SIyTeSrMtvFBBBliHhpuuj2BLt4iyXqNPmFj9jflbgaBxfSaqP4aXepiWetkzPMIw5xHeWeBo91MbsjeyHtMPKfAsIjRog2Cs8fKGWI2/gDITp8wmcO85tTwMJUbL9Pu1DxcYLryLRJUPRQTqjXXeMbAHzHT3zBu+zZ2mXwICIxbRSvMnYNIRLEQcB3Zecd5J4+XdOl+8BBxCZC0e9eZS741l7C6/PuAQBaGM7yD2t8wyM5SDd8cyX4ujSf5sdRbhKfSTfHWk7chJeyKbqTyHsZwCOEJOwbumu2mHHO8Dlp5Wkm+13TKQChRwKo9xfaWX6SOWZ5E4CIeaDTUysg8bg5xGqGPQvAGXe6D9P3hwBmEASaXHZZ6prEndYHIIDBEDjnvo8BMOtOPwypxgInerYDMMGfzrHn+JQOQqxmgmfb4VUgGDbJXyxwAzA8xwsYYI0F6oOLh0HgS6q8zSVusM7PvMcDfLXdZYbFCqcYKfIQD/CdsTe3rfdJ8nfIQ+qQs9ng2Mw+U33UCxHv8CuFHieIBjGwRrHn1TO02YMw6TZtxhMzzIymgYsOZgttgWOIv6nTobHj06FBkzriVNr9PwCuX8hVNtxtAAAAhGVYSWZNTQAqAAAACAAFARIAAwAAAAEAAQAAARoABQAAAAEAAABKARsABQAAAAEAAABSASgAAwAAAAEAAgAAh2kABAAAAAEAAABaAAAAAAAAAJAAAAABAAAAkAAAAAEAA6ABAAMAAAABAAEAAKACAAQAAAABAAAAIqADAAQAAAABAAAAIgAAAAAQQkDBAAAAJXRFWHRkYXRlOmNyZWF0ZQAyMDIyLTEyLTMwVDAwOjQ4OjU2KzAwOjAw6LvBaQAAACV0RVh0ZGF0ZTptb2RpZnkAMjAyMi0xMi0zMFQwMDo0ODo1NiswMDowMJnmedUAAAARdEVYdGV4aWY6Q29sb3JTcGFjZQAxD5sCSQAAABJ0RVh0ZXhpZjpFeGlmT2Zmc2V0ADkwWYzemwAAABd0RVh0ZXhpZjpQaXhlbFhEaW1lbnNpb24AMzRhz8IiAAAAF3RFWHRleGlmOlBpeGVsWURpbWVuc2lvbgAzNLxZG6cAAAAASUVORK5CYII=",
    7: f"{b64_prefix}MApGbEB/AAAAAW9yTlQBz6J3mgAAAulJREFUSMel1M9rHGUcx/H3M/PMTGY2a7o2oo2RxhbagxAIgZLSKGJR6k8iATdSSA9611IQ9KL4P3gQSnsoPfTQi6deiicP7cFA0hjBGFBBDyIibjbNbmY/Hp7ZyUyy2Q3mO7DzzH6f5zXPz4FimFIphCcu2X+9f6LX3NNhwsDr0cgpnp94xjU6M+cLIVR7CwgORYxW7ZoRTSt7DU7XEyHTooV8nXj3MIyB83H8M6Ltaaw+dTESMtsIsY0Cjc8fhgkg+RqR0nj601jIPEZDK+GKKxn59cGMBW4i2qRkhNk4Wx2tmg3EY4QYyFjgBqKN6LCNzPpIDWDiWPwTYgsxsDcWuJ4h26i2Nj0CWCxcqA6vdhkW+jERcAuxQwvF67O1vLKFyUr0KGfqB+2bEPz3u2tR/eFCFbD4eHj4e5nh93r1JgR/AbkJTFZfHgZsaQdbmE7CFccEenYfE0BYR65CxRE9Y5exGpsrDioAPyeGVicr/ZZwOrEryGwhX7W3u0wAcU4kjyYrwATqeX3hBhUsu9pGyZvZoEbfsdl0Ro6wjB+IgIXx2C67Fkb+G0B0yQjRQtHSC8PZbjkI+ay74GOJ/d61QpVXTfBX+0nTlo8Xz2w9IKQFVPmoMA0n+RCAh1ykka1lKzjXfkDHpAqSPxn6AyFSxAzg75tJn+8Q4jeO0/1s+cAMYgeh+HdOvBh8a9dQCfEKyCcI0eGVQqaLyKwH9596yf33QQkp9uY5mghxp9CzAuJddXIEaXTgtviSGEj5vHe6EwKRRwqonMlL41wG4B4/9siStUy9HrzyM7OYnY7bec7seSGA6YXs9mwegDbf7MuUojfi4jhTACyxSd/oh5zLhvUQ/j8yld03joKcze6/HgW5gsFguDsIsXtAP5uHnb71fdLi64tIA2gNeOlO/uvOs8qI+IpfCEs7QTRJgE0qhY82GFqcRBh3zmzuiVlmB42+FB3MLm2BRcTfNOjQHHh1aLJFA/Gxa/0fkVpL5ZBqUCMAAACEZVhJZk1NACoAAAAIAAUBEgADAAAAAQABAAABGgAFAAAAAQAAAEoBGwAFAAAAAQAAAFIBKAADAAAAAQACAACHaQAEAAAAAQAAAFoAAAAAAAAAkAAAAAEAAACQAAAAAQADoAEAAwAAAAEAAQAAoAIABAAAAAEAAAAioAMABAAAAAEAAAAiAAAAABBCQMEAAAAldEVYdGRhdGU6Y3JlYXRlADIwMjItMTItMzBUMDA6NDg6MTArMDA6MDAPIfqpAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDIyLTEyLTMwVDAwOjQ4OjEwKzAwOjAwfnxCFQAAABF0RVh0ZXhpZjpDb2xvclNwYWNlADEPmwJJAAAAEnRFWHRleGlmOkV4aWZPZmZzZXQAOTBZjN6bAAAAF3RFWHRleGlmOlBpeGVsWERpbWVuc2lvbgAzNGHPwiIAAAAXdEVYdGV4aWY6UGl4ZWxZRGltZW5zaW9uADM0vFkbpwAAAABJRU5ErkJggg==",
    8: f"{b64_prefix}Ly/AMpqmAAAAAW9yTlQBz6J3mgAAAz9JREFUSMeVlEuIHFUUhr9bdasqXd3tTMtgdAwYNRgkyWAc0EhmIfggvsIEIT1BcKEbwSwShYDoWhcuXIhIRMxCQRAEHwFXSnAjLnwwkzGCSQZRSQiGMUzPdLq6q38Xdfs13TPdOUVVn6o65zv3nvNXQ7eZHi+Emw7YFe9a9Hh2N4oZeCIau4s7t9+aJd0z6wshVHoaCEZCTBTtOSPWrOyrcHc5FjIJCfJ126FRMAYeyuUuIOqeJst7H4mETA0haijQtmdHwQQQn0SkVLa+lhMy19GWhXAh84z88nCMBU4h6qQ4hLm4szhRNBcR1xFiKMYCHyHqiCY1ZM6PlQC2j+f+QFQRQ1djgQ8dpIZK56bHAIuF/cXCYgvD3GaYCPgY0SBBufMzpXawhal8dLaNKW+kmxD8I61ZFH/bXwQsPh4e/npM4fCg1YTgz6GsgfHiwwXA9ijYwnQcLmSYQLf3YQIIyygLyGeIgdbBWE3Odm8qAL+N2LI4ld9shNOxXUCminyVnmlhAsi1EfHZqbybk88RvuVvEv7jJ97kllaLp+NgPos2ip9ym5o4aF07ow7Cchr1HFfY1cJsy9n5LMPIfxKIDhghEhT9sqvgEPCyS13iHX5w/vcdPU3G9ucsC+UfI7iKTEKKcg92NeoLl7gDCFhCiKYrACEEDyBSk6D4iucnoACgaoDUha263xpQpwrAMg039BTqHiAFoIZXOhycsb/j9YzA41PnfcPrfM69ALxL938fgG8uBN8V5jL/RYTYB/juhFeo9TT2lCvUitiHkHc8qxlBGvXJIeb+dbKe5dF+1TRDIPJIAfW+AT7gOQzwFuPMkgDjfMa4e9sxAanXT0cUyfZ5mTe4xpd8AsAYhzDrCgKYQRDY6vpy1dW97J5PDkAAgyGXXPJO9gAhB93zpYHRG0BWOQ2A5Qzv8yO73bq+vhEIHOUfAG7mJe4DoM4LrNwY5C/28DbzrNDkX37lJHv5aoPY9tfQb8uc4AQjWTfEA3wn7Mam8T5p9x66IRUgGVK00b5WACfTDkS8x5+EPUoQa8TAKvmeT8+QcAfCZHqybZ6YYWa0HjhrYjpoCzyPWKZCk7WhR5M1qlQQx7Ls/wFvw1d4y02SsgAAAIRlWElmTU0AKgAAAAgABQESAAMAAAABAAEAAAEaAAUAAAABAAAASgEbAAUAAAABAAAAUgEoAAMAAAABAAIAAIdpAAQAAAABAAAAWgAAAAAAAACQAAAAAQAAAJAAAAABAAOgAQADAAAAAQABAACgAgAEAAAAAQAAACKgAwAEAAAAAQAAACIAAAAAEEJAwQAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAyMi0xMi0zMFQwMDo0Nzo0NyswMDowMHNtkc4AAAAldEVYdGRhdGU6bW9kaWZ5ADIwMjItMTItMzBUMDA6NDc6NDcrMDA6MDACMClyAAAAEXRFWHRleGlmOkNvbG9yU3BhY2UAMQ+bAkkAAAASdEVYdGV4aWY6RXhpZk9mZnNldAA5MFmM3psAAAAXdEVYdGV4aWY6UGl4ZWxYRGltZW5zaW9uADM0Yc/CIgAAABd0RVh0ZXhpZjpQaXhlbFlEaW1lbnNpb24AMzS8WRunAAAAAElFTkSuQmCC",
    9: f"{b64_prefix}LwPy6vZFAAAAAW9yTlQBz6J3mgAAAzpJREFUSMeNk91rHFUYh58zc2YnO7truhCxpoVUBW1siUpEKwkiiKV+VFoq3Xgjov4BVkEQDfSi/gleCH7infTCu95p8cabkNBu0xRsIwUVv+pXt5vu7M7+vJiT2d1kN7u/gTnnzPu+z5nzvu+BbpmeWQ7uOGJvev+Gh9PVKDLwbDh+L/fs250G3X/MF0Ko/AIQjISYKNk1I+pW9m24rxIJmZgY+br7+CgYA0/k89cQTU+TlUeeDoVMAyEaKNDeE6NgAog+QiTU7no3L2Ruo7FqrprOjPzKcIwFPkM0SXAIs/5AaaJk1hG3EWIoxgKfIpqINg1kro6XAfbtyv+A2EAM/RsLfOwgDVRemx0HLBbmSsXVTQwLO2FC4EtEixjlr86XM2cLM4XwUoapDOqbHPgvb9aidHmuBFh8PDz8rZjiyX5/kwN/AaUJjFafKgK2p4MtzEa5aooJtGcbJoBcBaUOhRTRVx2M1eSx7kMF4GeIsdWZwk4lnI1sFZkN5Kt8dBMTQD5DRJdmCq5OY7zDEn9R50fOcrhTwdkouJh6G0XPu0NNvGhdOsMOYhcXUM/zQQezN28vphFG/nNAeMQIEaNw5UDRIdJSC7HC59xw86MdzGRkl9MoVHiG4AYyMQnKP54laiI1s4IF9pNew7XuWgaPIRITo+h3z49BAcCGARIAHnTFO0cLuML3AOxn2hU9gaYHSAGo5ZVPBuftFbyeEkRu9N3YcuPDXZ0D4JtrwTfFhXT+OkIccmE+Uy4Ll8kBe6i59VuZBxxCyDsF4BFCEm5phut8C8A0y3zCEpuds+2+tHNA6JEA6rUAb/AbAAd4jd387Cw1Z+1IQOKxXcKwzqN8wR80WOYlzjvLr5gtGwIY27e3BfzEq9n6fTcu90EAHv11mrMs8SdTwEPMAHCB9f7OdgDkTk4AcI7vOO62Oj3AdyDkPZ7kIDDNtPuyyNeDIIOO8w9znKFKjSa/8BVznGGg7EDLfyyyyEjqhniA7xq7taO/T9J9hm5IDYiHbNrK3jXAtWkHIj7kOrmeThB1IuAWhZ6rZ4iZQpj0itqMJ+aZHy0HTm1MB22BVxB/U6NNfejTps4GNcSbafT/ojtVLdMsay4AAACEZVhJZk1NACoAAAAIAAUBEgADAAAAAQABAAABGgAFAAAAAQAAAEoBGwAFAAAAAQAAAFIBKAADAAAAAQACAACHaQAEAAAAAQAAAFoAAAAAAAAAkAAAAAEAAACQAAAAAQADoAEAAwAAAAEAAQAAoAIABAAAAAEAAAAioAMABAAAAAEAAAAiAAAAABBCQMEAAAAldEVYdGRhdGU6Y3JlYXRlADIwMjItMTItMzBUMDA6NDc6MDIrMDA6MDClH7CTAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDIyLTEyLTMwVDAwOjQ3OjAyKzAwOjAw1EIILwAAABF0RVh0ZXhpZjpDb2xvclNwYWNlADEPmwJJAAAAEnRFWHRleGlmOkV4aWZPZmZzZXQAOTBZjN6bAAAAF3RFWHRleGlmOlBpeGVsWERpbWVuc2lvbgAzNGHPwiIAAAAXdEVYdGV4aWY6UGl4ZWxZRGltZW5zaW9uADM0vFkbpwAAAABJRU5ErkJggg==",
}

SERVER_URL_PATH = Path(__file__).parent / ".welcome_server_url"
try:
    SERVER_URL = SERVER_URL_PATH.read_text().strip()
except FileNotFoundError:
    raise RuntimeError("Server URL not set. Create a file called '.welcome_server_url' in the same directory as this script with the URL as the only content.")

WELCOME_DIR = Path.home() / ".welcome"
COOKIE_PATH = WELCOME_DIR / "cookies"
CACHE_DIR = WELCOME_DIR / "cache"


xbar_nesting = 0

@contextmanager
def xbar_submenu():
    global xbar_nesting

    xbar_nesting += 1
    try:
        yield
    finally:
        xbar_nesting -= 1

def xbar_sep():
    global xbar_nesting

    print("--" * xbar_nesting + "---", flush=True)

def xbar(text: Any | None = None, copy: bool | str = False, image: bytes | None = None, **params: Any):
    global xbar_nesting

    segments: list[str] = []

    if text:
        segments.append(str(text))

    if os.getenv("SWIFTBAR") != "1":
        params.pop("symbolize", None)

    # Copy value to clipboard (only tested on macOS)
    if copy:
        # TODO: Doesn't work properly with emojis and other non-ASCII characters
        copy_value = text if copy == True else copy
        params["bash"] = shutil.which("bash")
        params["param0"] = "-c"
        params["param1"] = f'"echo -n {str(copy_value)} | pbcopy"'
        params["terminal"] = False

    if image:
        params["image"] = base64.b64encode(image).decode()

    params_segments = [f"{key}={value}" for key, value in params.items() if value is not None]
    if params_segments:
        segments.append("|")
        segments.extend(params_segments)

    if segments:
        print("--" * xbar_nesting + " ".join(segments), flush=True)


def xbar_kv(label: str, value: Any, tabs: int = 0, **params: Any):
    if isinstance(value, list):
        value = ", ".join(cast(list[str], value))

    xbar("".join([label, "\t" * tabs, str(value)]), **params)


async def resize_image_data(data: bytes, size: int) -> bytes:
    if not shutil.which("sips"):
        return data

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        original_path = temp_dir_path / "original"
        resized_path = temp_dir_path / "resized"

        original_path.write_bytes(data)

        process = await asyncio.create_subprocess_exec(
            "sips",
            original_path,
            "-Z",
            str(size * 2),
            "-s",
            "dpiHeight",
            "144.0",
            "-s",
            "dpiWidth",
            "144.0",
            "--out",
            resized_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        await process.wait()

        data = resized_path.read_bytes()

    return data

async def circle_image_data(data: bytes) -> bytes:
    if not shutil.which("magick", path="/opt/homebrew/bin"):
        return data

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        original_path = temp_dir_path / "original"
        # circular_path = temp_dir_path / "circular"

        original_path.write_bytes(data)

        process = await asyncio.create_subprocess_exec(
            "magick",  # Requires ImageMagick
            original_path,
            "-alpha",
            "set",
            "-virtual-pixel",
            "transparent",
            "-channel",
            "A",
            "-fx",
            "hypot(i-w/2,j-h/2) < w/2 ? 1 : 0",
            "png:-",
            env={"PATH": "/opt/homebrew/bin"}, # TODO: Don't hardcode!
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        await process.wait()

        # TODO: Why does this not always return a modified image, even though the command works by itself?
        if process.stdout:
            data = await process.stdout.read()

    return data

async def read_url(url: str, session: aiohttp.ClientSession) -> bytes | None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    url_hash = hashlib.sha256(url.encode()).hexdigest()
    cache_file = CACHE_DIR / url_hash

    if cache_file.exists():
        return cache_file.read_bytes()

    try:
        async with session.get(URL(url, encoded=True)) as response:
            data = await response.read()
            cache_file.write_bytes(data)

            return data
    except (aiohttp.ClientConnectionError, aiohttp.ClientResponseError):
        return None

class Network(BaseModel):
    id: str
    display_name: str

    class Attrs(BaseModel):
        sf_symbol: str | None = None

    attrs: Attrs = Attrs()

    @property
    def sf_symbol(self) -> str | None:
        return self.attrs.sf_symbol

class DeviceType(str, Enum):
    phone = "phone"
    wearable = "wearable"
    handheld = "handheld"

    laptop = "laptop"
    tablet = "tablet"
    desktop = "desktop"

    other = "other"

    @property
    def sf_symbol(self) -> str | None:
        match self:
            case DeviceType.phone | DeviceType.handheld:
                return "iphone"
            case DeviceType.wearable:
                return "applewatch"

            case DeviceType.tablet:
                return "ipad"
            case DeviceType.desktop:
                return "desktopcomputer"
            case DeviceType.laptop:
                return "laptopcomputer"

            case _:
                return None

class Device(BaseModel):
    known: bool
    ids: list[str]
    display_name: str

    attrs: dict[str, Any] = {}

    type: DeviceType | None
    tracker: bool
    personal: bool

    @property
    def sf_symbol(self) -> str | None:
        return self.type.sf_symbol if self.type else None

class Person(BaseModel):
    known: bool
    id: str
    display_name: str

    avatar_url: str | None

    class Attrs(BaseModel):
        phone: str | None = None
        email: str | None = None
        door_code: str | int | None = None

        sf_symbol: str | None = None

    attrs: Attrs = Attrs()

    @property
    def sf_symbol(self) -> str | None:
        return self.attrs.sf_symbol

    async def avatar(self, session: aiohttp.ClientSession, size: int = 32) -> bytes | None:
        avatar_url = self.avatar_url
        if not avatar_url:
            return None

        data = await read_url(avatar_url, session)
        if not data:
            return None

        data = await resize_image_data(data, size)
        # TODO: Apply circle mask only on avatars, NOT on default device image (shouldn't be needed anyway?)
        data = await circle_image_data(data)

        return data

class Role(BaseModel):
    id: str
    display_name: str

    class Attrs(BaseModel):
        sf_symbol: str | None = None

    attrs: Attrs = Attrs()

    @property
    def sf_symbol(self) -> str | None:
        return self.attrs.sf_symbol

class Home(BaseModel):
    id: str
    display_name: str
    connected: bool | None = None

    class Attrs(BaseModel):
        class Wifi(BaseModel):
            ssid: str | None = None
            password: str | None = None

        class Address(BaseModel):
            street: str | None = None
            neighborhood: str | None = None
            postal_code: str | int | None = None
            city: str | None = None
            state: str | None = None
            country: str | None = None

            @property
            def google_maps_url(self) -> str | None:
                parts = [part for part in [self.street, self.neighborhood, str(self.postal_code), self.city, self.state, self.country] if part]
                query = ", ".join(parts)
                return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(query)}"

        class Link(BaseModel):
            label: str
            url: str

            class Attrs(BaseModel):
                sf_symbol: str | None = None
                roles: list[str] | None = None

            attrs: Attrs = Attrs()

            @property
            def sf_symbol(self) -> str | None:
                return self.attrs.sf_symbol

            @property
            def roles(self) -> list[str] | None:
                return self.attrs.roles

        links: list[Link] = []

        address: Address | None = None
        wifi: Wifi | None = None

        class DoorCode(BaseModel):
            prefix: str | None = None
            code: str | int | None = None

        door_code: DoorCode | None = None

        avatar_url: str | None = None

    attrs: Attrs = Attrs()

    def door_code(self, person: Person | None = None) -> str | None:
        door_code = self.attrs.door_code
        if not door_code:
            return None

        code = door_code.code or (person and person.attrs.door_code)

        if not code:
            return None

        code = str(code)
        if prefix := door_code.prefix:
            code = prefix + code

        return code

    @property
    def avatar_url(self) -> str | None:
        return self.attrs.avatar_url

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Home):
            return self.id == other.id
        return False

    async def avatar(self, session: aiohttp.ClientSession, size: int = 32) -> bytes | None:
        avatar_url = self.avatar_url
        if not avatar_url:
            return None

        data = await read_url(avatar_url, session)
        if not data:
            return None

        data = await resize_image_data(data, size)

        return data

class Room(BaseModel):
    id: str
    display_name: str

    class Attrs(BaseModel):
        sf_symbol: str | None = None

    attrs: Attrs = Attrs()

    @property
    def sf_symbol(self) -> str | None:
        return self.attrs.sf_symbol

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Room):
            return self.id == other.id
        return False

class Metadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    ip: str | None = None
    mac: str | None = None
    mac_is_private: bool = False
    wifi_ssid: str | None = None

    country: CountryAlpha2 | None = None

class Connection(BaseModel):
    summary: str

    known: bool

    active_ids: list[str]
    known_active_ids: list[str]

    network: Network

    device: Device
    person: Person | None = None

    role: Role

    home: Home | None = None
    room: Room | None = None

    metadata: Metadata

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Connection):
            return self.network.id == other.network.id and self.active_ids == other.active_ids
        return False

class ConnectedPerson(BaseModel):
    known: bool

    person: Person

    home: Home | None = None
    room: Room | None = None

    role: Role

    connection: Connection

class WelcomeApp:
    def __init__(self):
        self._connection: Connection | None = None
        self._homes: list[Home] | None = None
        self._my_connections: list[Connection] | None = None
        self._connected_people: list[ConnectedPerson] | None = None
        self._person_connections: dict[str, list[Connection]] = defaultdict(list)
        self._device_connections: dict[str, list[Connection]] = defaultdict(list)

        self._session: aiohttp.ClientSession | None = None
        self._cookie_jar = CookieJar()
        self._load_cookies()

    def _load_cookies(self) -> None:
        try:
            if COOKIE_PATH.exists():
                with COOKIE_PATH.open('rb') as f:
                    cookies = pickle.load(f)
                    self._cookie_jar.update_cookies(cookies)
        except:
            pass

    def _save_cookies(self) -> None:
        try:
            with COOKIE_PATH.open('wb') as f:
                cookies = self._cookie_jar.filter_cookies(URL(SERVER_URL))
                pickle.dump(cookies, f)
        except:
            pass

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession(
                raise_for_status=True,
                cookie_jar=self._cookie_jar
            )

        return self._session

    async def request(self, url: str, raise_for_status: bool = False) -> list[dict[str, Any]] | dict[str, Any] | None:
        try:
            response = await self.session.get(url)
            self._save_cookies()

            return await response.json()
        except (aiohttp.ClientConnectionError, aiohttp.ClientResponseError):
            if raise_for_status:
                raise
            return None

    @property
    async def connection(self) -> Connection:
        if self._connection is None:
            raw_connection = await self.request(f"{SERVER_URL}/api/me", raise_for_status=True)
            self._connection = Connection.model_validate(raw_connection)

        return self._connection

    @property
    async def homes(self) -> list[Home]:
        if self._homes is None:
            raw_homes = await self.request(f"{SERVER_URL}/api/homes") or []
            self._homes = [Home.model_validate(raw) for raw in raw_homes]

        return self._homes

    @property
    async def my_connections(self) -> list[Connection]:
        if self._my_connections is None:
            raw_connections = await self.request(f"{SERVER_URL}/api/me/connections") or []
            self._my_connections = [Connection.model_validate(raw) for raw in raw_connections]

        return self._my_connections

    @property
    async def connected_people(self) -> list[ConnectedPerson]:
        if self._connected_people is None:
            raw_people = await self.request(f"{SERVER_URL}/api/homes/people") or []
            self._connected_people = [ConnectedPerson.model_validate(raw) for raw in raw_people]

        return self._connected_people

    async def device_connections(self, device: Device) -> list[Connection]:
        if not device.known:
            return []

        id = device.ids[0]
        if id not in self._device_connections:
            raw_connections = await self.request(f"{SERVER_URL}/api/devices/{id}/connections") or []
            self._device_connections[id] = [Connection.model_validate(raw) for raw in raw_connections]

        return self._device_connections[id]

    async def person_connections(self, person: Person) -> list[Connection]:
        if not person.known:
            return []

        if person.id not in self._person_connections:
            raw_connections = await self.request(f"{SERVER_URL}/api/people/{person.id}/connections") or []
            self._person_connections[person.id] = [Connection.model_validate(raw) for raw in raw_connections]

        return self._person_connections[person.id]

    @property
    async def home_room_people(self) -> OrderedDict[Home, OrderedDict[Room | None, list[ConnectedPerson]]]:
        home_room_people: OrderedDict[Home, OrderedDict[Room | None, list[ConnectedPerson]]] = OrderedDict()

        people = await self.connected_people
        for person in people:
            if person.home:
                home_room_people.setdefault(person.home, OrderedDict()).setdefault(person.room, []).append(person)

        # Include all homes
        homes = await self.homes
        for home in homes:
            if home in home_room_people:
                continue

            if home.connected is False:
                continue

            home_room_people.setdefault(home, OrderedDict())

        connection = await self.connection
        my_connections = await self.my_connections

        # Always include the current home and list it first
        home = next((conn.home for conn in [*my_connections, connection] if conn.home), None)
        if home:
            home_room_people.setdefault(home, OrderedDict())
            home_room_people.move_to_end(home, last=False)

        return home_room_people

    async def xbar_welcome(self):
        connection = await self.connection

        prefix = "Welcome **"
        suffix = "**"

        if role_icon := connection.role.sf_symbol:
            suffix += f" :{role_icon}:"
        if network_icon := connection.network.sf_symbol:
            suffix += f" :{network_icon}:"

        params: dict[str, Any] = {"md": True, "prefix": prefix, "suffix": suffix, "href": SERVER_URL}
        if connection.person:
            await self.xbar_person(connection.person, **params)
        else:
            self.xbar_device(connection.device, **params)

    async def xbar_welcome_details(self):
        connection = await self.connection

        self.xbar_network(connection.network)

        with xbar_submenu():
            await self.xbar_connection_details(connection)

        await self.xbar_other_connections()

        if person := connection.person:
            xbar_sep()
            await self.xbar_person_devices(person)

    async def xbar_person_devices(self, person: Person):
        person_connections = await self.person_connections(person)
        if len(person_connections) <= 1:
            return

        xbar("Devices", sfimage="macbook.and.iphone")

        with xbar_submenu():
            for conn in person_connections:
                self.xbar_connection(conn)

                with xbar_submenu():
                    await self.xbar_connection_details(conn)

    async def xbar_other_connections(self):
        connection = await self.connection
        my_connections = await self.my_connections
        other_connections = [conn for conn in my_connections if conn != connection]
        if not other_connections:
            return

        xbar_sep()
        xbar(f"Other Connections")

        for conn in other_connections:
            self.xbar_network(conn.network)

            with xbar_submenu():
                await self.xbar_connection_details(conn)

    async def xbar_home(self, home: Home, avatar: bool = True, **params: Any):
        if avatar and (image := await home.avatar(self.session, size=20)):
            params["image"] = image
        else:
            params["sfimage"] = "house"

        xbar(home.display_name, **params)

    async def xbar_home_details(self, home: Home):
        connection = await self.connection

        links = home.attrs.links
        filtered_links = [link for link in links if not link.roles or connection.role.id in link.roles]
        if filtered_links:
            for link in filtered_links:
                xbar(link.label, href=link.url, sfimage=link.sf_symbol)
            xbar_sep()

        address = home.attrs.address
        if address:
            xbar("Google Maps", href=address.google_maps_url, sfimage="map")

            xbar("Address", sfimage="mappin.and.ellipse")
            with xbar_submenu():
                if address.street:
                    xbar(address.street, copy=True, sfimage="house")
                if address.neighborhood:
                    xbar(address.neighborhood, copy=True, sfimage="house.circle")
                if address.postal_code:
                    xbar(str(address.postal_code), copy=True, sfimage="mail.and.text.magnifyingglass")
                if address.city:
                    xbar(address.city, copy=True, sfimage="building.2")
                if address.state:
                    xbar(address.state, copy=True, sfimage="building.columns")
                if address.country:
                    xbar(address.country, copy=True, sfimage="flag.circle")

        connection = await self.connection
        if code := home.door_code(connection.person):
            xbar_sep()
            xbar("Door Code", sfimage="lock")
            with xbar_submenu():
                xbar(code, copy=True)

        wifi = home.attrs.wifi
        if wifi:
            xbar_sep()
            xbar("Wi-Fi", sfimage="wifi")
            with xbar_submenu():
                if wifi.ssid:
                    xbar(wifi.ssid, sfimage="wifi.circle", copy=True)
                if wifi.password:
                    xbar(wifi.password, sfimage="key.horizontal", copy=True)

    def xbar_room(self, room: Room, **params: Any):
        xbar(room.display_name, sfimage=room.sf_symbol or "door.left.hand.open", **params)

    async def xbar_person(self, person: Person, avatar_size: int = 20, prefix: str = "", suffix: str = "", **params: Any):
        avatar = await person.avatar(self.session, size=avatar_size)
        if avatar:
            params["image"] = avatar
        else:
            params["sfimage"] = person.sf_symbol or ("person.fill" if person.known else "person.fill.questionmark")

        xbar(prefix + person.display_name + suffix, **params)

    async def xbar_person_details(self, person: Person):
        if code := person.attrs.door_code:
            xbar(code, sfimage="lock", copy=True)

        phone = person.attrs.phone
        email = person.attrs.email
        if phone or email:
            xbar_sep()
            if phone:
                phone = phone.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
                xbar("WhatsApp", href=f"https://wa.me/{phone}", sfimage="message")
                xbar("Call", href=f"tel:{phone}", sfimage="phone")
            if email:
                xbar("Email", href=f"mailto:{email}", sfimage="envelope")

    def xbar_device(self, device: Device, prefix: str = "", suffix: str = "", **params: Any):
        xbar(prefix + device.display_name + suffix, sfimage=device.sf_symbol or "externaldrive.badge.questionmark", **params)

    def xbar_role(self, role: Role, label: str | None = None):
        xbar(label or role.display_name, sfimage=role.sf_symbol or "person.circle")

    def xbar_network(self, network: Network, label: str | None = None):
        xbar(label or network.display_name, sfimage=network.sf_symbol or "network")

    def xbar_connection(self, conn: Connection, prefix: str = "", suffix: str = "", **params: Any):
        if (icon := conn.network.sf_symbol):
            prefix = f":{icon}: " + prefix
        else:
            suffix += f" @ {conn.network.display_name}"

        self.xbar_device(conn.device, prefix, suffix, **params)

    async def xbar_connection_details(self, conn: Connection):
        xbar_sep()
        xbar("Known" if conn.known else "Unknown", sfimage="person.fill.checkmark" if conn.known else "person.fill.questionmark")
        self.xbar_role(conn.role)
        self.xbar_network(conn.network)
        self.xbar_device(conn.device)

        if conn.home:
            xbar_sep()
            await self.xbar_home(conn.home, avatar=False)
            if conn.room:
                self.xbar_room(conn.room)

        metadata = conn.metadata

        xbar_sep()
        if metadata.ip:
            xbar(metadata.ip, sfimage="externaldrive.connected.to.line.below", copy=True)
        if metadata.mac:
            xbar(metadata.mac, sfimage="externaldrive.badge.questionmark" if metadata.mac_is_private else "externaldrive", copy=True, symbolize=False, emojize=False)
        if metadata.wifi_ssid:
            xbar(metadata.wifi_ssid, sfimage="wifi.circle")
        if metadata.country:
            xbar(metadata.country.short_name, sfimage="flag.circle")

        xbar_sep()
        xbar("More Info", sfimage="info.circle")
        with xbar_submenu():
            xbar("Summary", sfimage="text.magnifyingglass")
            with xbar_submenu():
                xbar(conn.summary, symbolize=False, emojize=False)

            xbar_sep()
            xbar(", ".join(conn.active_ids) if conn.active_ids else "No Active IDs", tabs=2, sfimage="externaldrive.badge.wifi", symbolize=False, emojize=False)
            xbar(", ".join(conn.known_active_ids) if conn.known_active_ids else "No Known Active IDs", tabs=1, sfimage="externaldrive.badge.checkmark", symbolize=False, emojize=False)

            xbar_sep()
            for key, value in metadata.model_dump().items():
                xbar_kv(f"{key} = ", value, symbolize=False, emojize=False)

    def xbar_icon(self, device_count: int | None = None):
        xbar(templateImage=MENUBAR_NUMBER_ICONS_B64.get(device_count or -1, MENUBAR_ICON_B64))
        xbar_sep()

    def xbar_refresh(self, **params: Any):
        xbar("Refresh", refresh=True, **params)

    def xbar_open(self, **params: Any):
        xbar("Open Welcome...", href=SERVER_URL, **params)

    def xbar_error(self, message: str, err: Exception | None = None, **params: Any):
        xbar(message, sfimage="warning", color="red", **params)
        if err:
            print(err)

    def xbar_footer(self):
        xbar_sep()
        self.xbar_refresh()
        self.xbar_open()

async def main():
    app = WelcomeApp()

    try:
        try:
            await app.connection
        except (aiohttp.ClientConnectionError, aiohttp.ClientResponseError) as err:
            app.xbar_icon()
            app.xbar_error("Failed to connect to Welcome server", err)
            app.xbar_footer()

            return

        people = await app.connected_people
        app.xbar_icon(len(people))

        await app.xbar_welcome()
        with xbar_submenu():
            await app.xbar_welcome_details()

            app.xbar_footer()

        home_room_people = await app.home_room_people
        for home, room_people in home_room_people.items():
            xbar_sep()

            await app.xbar_home(home, size=15)
            with xbar_submenu():
                await app.xbar_home_details(home)

            for room, people in room_people.items():
                xbar_sep()

                if room:
                    app.xbar_room(room)

                for connected_person in people:
                    person = connected_person.person
                    conn = connected_person.connection

                    await app.xbar_person(person, avatar_size=26)
                    with xbar_submenu():
                        app.xbar_role(conn.role)

                        await app.xbar_person_details(person)

                        xbar_sep()

                        app.xbar_network(conn.network, label="Connection")
                        with xbar_submenu():
                            await app.xbar_connection_details(conn)

                        await app.xbar_person_devices(person)
    finally:
        # TODO: Make app context manager?
        await app.session.close()

if __name__ == "__main__":
    asyncio.run(main())
