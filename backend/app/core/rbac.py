from fastapi import Depends, HTTPException, status

from backend.app.api.deps import get_current_user


def require_roles(*required_roles: str):
    def _checker(user=Depends(get_current_user)):
        user_role_names = {role.name for role in user.roles}
        if not user_role_names.intersection(required_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient role')
        return user

    return _checker
