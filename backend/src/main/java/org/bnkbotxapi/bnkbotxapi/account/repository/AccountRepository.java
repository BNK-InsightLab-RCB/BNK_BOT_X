package org.bnkbotxapi.bnkbotxapi.account.repository;

import org.bnkbotxapi.bnkbotxapi.account.domain.AccountEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface AccountRepository extends JpaRepository<AccountEntity, Long> {

    Optional<AccountEntity> findByLoginIdAndDeletedFalse(String loginId);

    Optional<AccountEntity> findByRefreshTokenAndDeletedFalse(String refreshToken);

    boolean existsByLoginId(String loginId);
}
